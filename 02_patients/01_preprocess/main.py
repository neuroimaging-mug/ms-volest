from research_groups import get_research_groups
from workflow import preprocess

STUDY_BASE_PATH = '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen'

preprocess(
  get_research_groups(),
  {
    'T1': STUDY_BASE_PATH + '/{research_group}/{subject_folder}/T1.nii.gz',
    'FLAIR': STUDY_BASE_PATH + '/{research_group}/{subject_folder}/FLAIR_re.nii.gz',
    'FLAIR_mask': STUDY_BASE_PATH + '/{research_group}/{subject_folder}/FLAIR_mask_raw.nii',
  },
  '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/data_preprocessed_extra_pat',
  12,
)
