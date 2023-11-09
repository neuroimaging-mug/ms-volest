import os
import json
import subprocess
from multiprocessing.pool import ThreadPool

PROCESSES = 12
STUDY_BASE_PATH = '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/data_preprocessed'

with open('fails.json') as infile:
  fails = json.load(infile)

subjects = []
for fail in fails:
  fail_path = os.path.join(STUDY_BASE_PATH, fail)
  subjects.append(fail_path)

def run_preprocess(fail):
  # create dummy mask
  cmd_parts = [
    'fslmaths',
    os.path.join(STUDY_BASE_PATH, fail, 'FLAIR__reoriented__mask__@T1__reoriented__bin.nii.gz'),
    '-mul',
    '0',
    '-add',
    '1',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__wm_mask_dummy.nii.gz'),
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, fail), shell=True)

  # lesion_filling -i	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1.nii.gz	
  # -w	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1_sienax/I_stdmaskbrain_pve_2.nii.gz	
  # -l	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/FLAIR_masktoT1_bin_fill.nii.gz	
  # -o	/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/MRT_FU/1000014729/T1_filled.nii.gz
  cmd_parts = [
    'lesion_filling',
    '-i',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented.nii.gz'),
    '-w',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__wm_mask_dummy.nii.gz'),
    '-l',
    os.path.join(STUDY_BASE_PATH, fail, 'FLAIR__reoriented__mask__@T1__reoriented__bin.nii.gz'),
    '-o',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented__filled.nii.gz'),
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, fail), shell=True)

  # noNeck
  cmd_parts = [
    'fslmaths',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented__filled.nii.gz'),
    '-mas',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented__noNeck__mask.nii.gz'),
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented__filled__noNeck.nii.gz'),
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, fail), shell=True)

  # sienax on filled
  cmd_parts = [
    'sienax',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__reoriented__filled__noNeck.nii.gz'),
    '-o',
    os.path.join(STUDY_BASE_PATH, fail, 'T1__filled__sienax_f0.35'),
    '-d',
    '-B',
    '\"-f 0.35 -B\"',
    '-r',
  ]
  cmd = ' '.join(cmd_parts)
  print(cmd)
  subprocess.run(cmd, cwd=os.path.join(STUDY_BASE_PATH, fail), shell=True)
  
  return fail + ' done'

pool = ThreadPool(PROCESSES)
results = [pool.apply_async(run_preprocess, (fail,)) for fail in subjects]

pool.close()
pool.join()

for result in results:
  print(result.get())
