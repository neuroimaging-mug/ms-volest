import os
import subprocess
from multiprocessing.pool import ThreadPool

PROCESSES = 12
STUDY_BASE_PATH = '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/data_preprocessed_extra_pat'

subjects = []
for study in ['MRT_BL', 'MRT_FU']:
  study_path = os.path.join(STUDY_BASE_PATH, study)

  subject_folders = os.listdir(study_path)
  subject_folders.sort()

  for subject_folder in subject_folders:
    subjects.append((study, subject_folder))

def run_preprocess(study, subject):
  # sienax
  cmd_parts = [
    'sienax',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__noNeck.nii.gz'),
    '-o',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__sienax_f0.35'),
    '-d',
    '-B',
    '\"-f 0.35 -B\"',
    '-r',
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, study, subject), shell=True)

  # lesion_filling -i	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1.nii.gz	
  # -w	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1_sienax/I_stdmaskbrain_pve_2.nii.gz	
  # -l	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/FLAIR_masktoT1_bin_fill.nii.gz	
  # -o	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1_filled.nii.gz
  cmd_parts = [
    'lesion_filling',
    '-i',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented.nii.gz'),
    '-w',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__sienax_f0.35', 'I_stdmaskbrain_pve_2.nii.gz'),
    '-l',
    os.path.join(STUDY_BASE_PATH, study, subject, 'FLAIR__reoriented__mask__@T1__reoriented__bin.nii.gz'),
    '-o',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__filled.nii.gz'),
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, study, subject), shell=True)

  # noNeck
  cmd_parts = [
    'fslmaths',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__filled.nii.gz'),
    '-mas',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__noNeck__mask.nii.gz'),
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__filled__noNeck.nii.gz'),
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, study, subject), shell=True)

  # sienax on filled
  cmd_parts = [
    'sienax',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__reoriented__filled__noNeck.nii.gz'),
    '-o',
    os.path.join(STUDY_BASE_PATH, study, subject, 'T1__filled__sienax_f0.35'),
    '-d',
    '-B',
    '\"-f 0.35 -B\"',
    '-r',
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, study, subject), shell=True)
  
  return study + '/' + subject + ' done'

pool = ThreadPool(PROCESSES)
results = [pool.apply_async(run_preprocess, (study, subject)) for (study, subject) in subjects]

pool.close()
pool.join()

for result in results:
  print(result.get())
