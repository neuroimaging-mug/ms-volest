import os
import json

STUDY_BASE_PATH = '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/data_preprocessed'

fails = []
for study in ['MRT_BL', 'MRT_FU']:
  study_path = os.path.join(STUDY_BASE_PATH, study)

  subject_folders = os.listdir(study_path)
  subject_folders.sort()

  for subject_folder in subject_folders:
    if not os.path.exists(os.path.join(study_path, subject_folder, 'T1__filled__sienax_f0.35')):
      fails.append(study + '/' + subject_folder)

with open('fails.json', 'w') as outfile:
  json.dump(fails, outfile, indent=2)
