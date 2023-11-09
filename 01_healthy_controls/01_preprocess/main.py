from research_groups import get_research_groups
from workflow import preprocess

STUDY_BASE_PATH = '/media/DSraid/MS_GRAZ/MRI_DATA/CANDI_workflow/FATIGUE_Steffi'

preprocess(
  get_research_groups(),
  {
    'T1': STUDY_BASE_PATH + '/{research_group}/{subject_folder}/T1.nii.gz',
  },
  '/media/DSraid/Hechenberger/MS_Studien/PST/Analysen/data_preprocessed_HC',
  12,
)
