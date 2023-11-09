import os

from nipype.interfaces.utility import IdentityInterface, Function, Select
from nipype.interfaces.io import SelectFiles, DataSink
from nipype.pipeline.engine import Workflow, Node
from nipype.interfaces.fsl import FLIRT, ApplyXFM, FIRST
from nipype.interfaces.fsl.maths import ApplyMask, Threshold, UnaryMaths
from nipype.interfaces.fsl.utils import Reorient2Std, ConvertXFM

# get container
def datasink_container_from_identity(research_group, subject_folder):
  return research_group + '/' + subject_folder

def build_selectfiles_workflow(research_groups, select_templates, name='selectfiles'):
  # identities
  research_group_identity_node = Node(IdentityInterface(
    fields=['research_group'],
  ), name=name + '__research_group_identity')
  research_group_identity_node.iterables = [
    ('research_group', research_groups['research_group']),
  ]

  subject_identity_node = Node(IdentityInterface(
    fields=['research_group', 'subject_folder'],
  ), name=name + '__subject_identity')
  subject_identity_node.itersource = (name + '__research_group_identity', 'research_group')
  subject_identity_node.iterables = [('subject_folder', research_groups['subject_folder'])]
  
  # select files
  selectfiles_node = Node(SelectFiles(
    select_templates,
    sort_filelist=True,
    force_lists=['T1'],
  ), name=name + '__selectfiles')

  # datasink container
  datasink_container_node = Node(Function(
    input_names=['research_group', 'subject_folder'],
    output_names=['container'],
    function=datasink_container_from_identity,
  ), name=name + '__datasink_container')

  # select files subworkflow
  selectfiles_worklow = Workflow(name)
  selectfiles_worklow.connect([
    (research_group_identity_node, subject_identity_node,   [('research_group', 'research_group')]),
    (subject_identity_node, selectfiles_node,               [
                                                              ('research_group', 'research_group'),
                                                              ('subject_folder', 'subject_folder'),
                                                            ]),
    (subject_identity_node, datasink_container_node,        [
                                                              ('research_group', 'research_group'),
                                                              ('subject_folder', 'subject_folder'),
                                                            ]),
  ])

  return selectfiles_worklow

def build_datasink_node(target_base_dir, workflow_name):
  return Node(DataSink(
    base_directory=target_base_dir,
    parameterization=False,
    substitutions=[
      ('T1_reoriented.nii.gz', 'T1__reoriented.nii.gz'),
      ('T1__noNeck/T1_reoriented_masked.nii.gz', 'T1__reoriented__noNeck.nii.gz'),
      ('T1__forward_backward/T1_reoriented_flirt_flirt.nii.gz', 'T1__reoriented__noNeck__forward_backward.nii.gz'),
      ('T1__noNeck__mask/T1_reoriented_flirt_flirt_bin.nii.gz', 'T1__reoriented__noNeck__mask.nii.gz'),
      
      ('T1__FIRST_segmentation_file/segmented_all_fast_firstseg.nii.gz', 'T1__reoriented__FIRST_segmentation.nii.gz'),
      ('T1__FIRST_original_segmentations/segmented_all_fast_origsegs.nii.gz', 'T1__reoriented__FIRST_original_segmentation.nii.gz'),
      
      ('regMPRAGE_dof6/T1_reoriented_flirt.nii.gz', 'T1__reoriented__@MNI__dof6.nii.gz'),
      ('regMatrix_dof6/T1_reoriented_flirt.mat', 'T1__reoriented__2MNI__dof6.mat'),
      ('inv_regMatrix_dof6/T1_reoriented_flirt_inv.mat', 'MNI152__2T1__reoriented__dof6.mat'),

      ('FLAIR_mask_bin/FLAIR_mask_raw_thresh_bin.nii.gz', 'FLAIR__reoriented__mask__bin.nii.gz'),
      ('FLAIR_mask_at_T1_bin/FLAIR_mask_raw_thresh_bin_flirt_bin.nii.gz', 'FLAIR__reoriented__mask__@T1__reoriented__bin.nii.gz'),
      ('FLAIR_at_T1_dof6/FLAIR_re_flirt.nii.gz', 'FLAIR__reoriented__@T1__reoriented.nii.gz'),
      ('FLAIR_at_T1_dof6_matrix/FLAIR_re_flirt.mat', 'FLAIR__reoriented__2T1__reoriented.mat'),
    ],
    regexp_substitutions=[],
  ), name=workflow_name + '__datasink')

def preprocess(studies, select_templates, target_base_dir, processor_count=1):
  # preprocess workflow
  preprocess_workflow = Workflow(
    name='preprocess_part1',
    base_dir=os.path.join(target_base_dir, 'tmp')
  )

  # selectfiles subworkflow
  selectfiles_workflow = build_selectfiles_workflow(
    studies, select_templates,
  )

  # datasink
  datasink_node = build_datasink_node(target_base_dir, 'T1')

  # select first T1
  select_first_T1_node = Node(Select(
    index=[0],
  ), name='T1__select_first_T1')

  # fslreorient2std <input> <output>
  reorient2std_node = Node(Reorient2Std(), name='T1__reorient2std')

  # flirt -cost corratio -dof 6 -in <input> -ref <reference> -out <output> -omat <outputmatrix>
  reg_to_MNI_dof6_node = Node(FLIRT(
    cost='corratio',
    dof=6,
    reference='/usr/local/fsl/data/standard/MNI152_T1_1mm.nii.gz',
  ), name='T1__reg_to_MNI_dof6')

  # convert_xfm -omat <output> -inverse <input>
  invert_xfm_node = Node(ConvertXFM(
    invert_xfm=True,
  ), name='T1__invert_xfm')

  # flirt -applyxfm -in <input> -ref <reference> -init <dof6_matrix> -out <output>
  apply_to_T1_node = Node(ApplyXFM(
    apply_xfm=True,
  ), name='T1__apply_to_T1')

  # fslmaths <input> -bin <output>
  bin_node = Node(UnaryMaths(
    operation='bin',
  ), name='T1__bin')

  # fslmaths <input> -mul <mask> <output>
  mask_node = Node(ApplyMask(
  ), name='T1__mask')

  # run_first_all -i <input> -o <output>
  first_node = Node(FIRST(
  ), name='T1__FIRST')

  # fslmaths <input> -thr 0.25 <output>
  FLAIR_mask_thresh_node = Node(Threshold(
    thresh=0.25,
    direction='below',
    output_type='NIFTI_GZ',
  ), name='T1__FLAIR_thresh')

  # fslmaths <input> -bin <output>
  FLAIR_mask_bin_node = Node(UnaryMaths(
    operation='bin',
  ), name='T1__FLAIR_bin')

  # fslmaths <input> -binv <output>
  FLAIR_mask_binv_node = Node(UnaryMaths(
    operation='binv',
  ), name='T1__FLAIR_bin_inverted')

  # flirt -cost mutualinfo -dof 6 -in <input> -inweight <inputweighting> -ref <reference> -searchx -15 15 -searchy -15 15 -searchz -15 15 -out <output> -omat <outputmatrix>
  FLAIR_to_T1_dof6_node = Node(FLIRT(
    cost='mutualinfo',
    dof=6,
    searchr_x=[-15, 15],
    searchr_y=[-15, 15],
    searchr_z=[-15, 15],
  ), name='T1__FLAIR_to_T1_dof6')

  # flirt -applyxfm -in <input> -ref <reference> -init <dof6_matrix> -out <output>
  T1__FLAIR_mask_to_T1_dof6_node = Node(ApplyXFM(
    apply_xfm=True,
  ), name='T1__FLAIR_mask_to_T1_dof6')

  # fslmaths <input> -bin <output>
  FLAIR_mask_at_T1_bin_node = Node(UnaryMaths(
    operation='bin',
    output_datatype='short',
  ), name='T1__FLAIR_mask_on_T1_bin')

  # T1
  preprocess_workflow.connect([
    (selectfiles_workflow, datasink_node,                           [('selectfiles__datasink_container.container', 'container')]),

    (selectfiles_workflow, select_first_T1_node,                    [('selectfiles__selectfiles.T1', 'inlist')]),
    
    (select_first_T1_node, reorient2std_node,                       [('out', 'in_file')]),
    (reorient2std_node, reg_to_MNI_dof6_node,                       [('out_file', 'in_file')]),
    (reg_to_MNI_dof6_node, invert_xfm_node,                         [('out_matrix_file', 'in_file')]),
    (invert_xfm_node, apply_to_T1_node,                             [('out_file', 'in_matrix_file')]),
    (reg_to_MNI_dof6_node, apply_to_T1_node,                        [('out_file', 'in_file')]),
    (reorient2std_node, apply_to_T1_node,                           [('out_file', 'reference')]),
    
    (apply_to_T1_node, bin_node,                                    [('out_file', 'in_file')]),
    (reorient2std_node, mask_node,                                  [('out_file', 'in_file')]),
    (bin_node, mask_node,                                           [('out_file', 'mask_file')]),

    (reorient2std_node, first_node,                                 [('out_file', 'in_file')]),

    (reorient2std_node, datasink_node,                              [('out_file', '@T1')]),
    (reg_to_MNI_dof6_node, datasink_node,                           [('out_matrix_file', 'regMatrix_dof6')]),
    (reg_to_MNI_dof6_node, datasink_node,                           [('out_file', 'regMPRAGE_dof6')]),
    (invert_xfm_node, datasink_node,                                [('out_file', 'inv_regMatrix_dof6')]),
    (apply_to_T1_node, datasink_node,                               [('out_file', 'T1__forward_backward')]),
    (bin_node, datasink_node,                                       [('out_file', 'T1__noNeck__mask')]),
    (mask_node, datasink_node,                                      [('out_file', 'T1__noNeck')]),
    (first_node, datasink_node,                                     [('original_segmentations', 'T1__FIRST_original_segmentations')]),
    (first_node, datasink_node,                                     [('segmentation_file', 'T1__FIRST_segmentation_file')]),

    #part 2
    (selectfiles_workflow, FLAIR_mask_thresh_node,                  [('selectfiles__selectfiles.FLAIR_mask', 'in_file')]),
    (FLAIR_mask_thresh_node, FLAIR_mask_bin_node,                   [('out_file', 'in_file')]),
    (FLAIR_mask_bin_node, FLAIR_mask_binv_node,                     [('out_file', 'in_file')]),

    (selectfiles_workflow, FLAIR_to_T1_dof6_node,                   [('selectfiles__selectfiles.FLAIR', 'in_file')]),
    (reorient2std_node, FLAIR_to_T1_dof6_node,                      [('out_file', 'reference')]),
    (FLAIR_mask_binv_node, FLAIR_to_T1_dof6_node,                   [('out_file', 'in_weight')]),

    (FLAIR_mask_bin_node, T1__FLAIR_mask_to_T1_dof6_node,           [('out_file', 'in_file')]),
    (reorient2std_node, T1__FLAIR_mask_to_T1_dof6_node,             [('out_file', 'reference')]),
    (FLAIR_to_T1_dof6_node, T1__FLAIR_mask_to_T1_dof6_node,         [('out_matrix_file', 'in_matrix_file')]),

    (T1__FLAIR_mask_to_T1_dof6_node, FLAIR_mask_at_T1_bin_node,     [('out_file', 'in_file')]),

    (FLAIR_to_T1_dof6_node, datasink_node,                          [('out_file', 'FLAIR_at_T1_dof6')]),
    (FLAIR_to_T1_dof6_node, datasink_node,                          [('out_matrix_file', 'FLAIR_at_T1_dof6_matrix')]),
    (FLAIR_mask_bin_node, datasink_node,                            [('out_file', 'FLAIR_mask_bin')]),
    (FLAIR_mask_at_T1_bin_node, datasink_node,                      [('out_file', 'FLAIR_mask_at_T1_bin')]),
  ])

  preprocess_workflow.write_graph(dotfilename='./graphs/preprocess.dot', graph2use='orig', simple_form=True)
  preprocess_workflow.run('MultiProc', plugin_args={'n_procs': processor_count})
