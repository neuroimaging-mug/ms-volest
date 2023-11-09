import json

def get_research_groups():
  with open('HC.json', 'r') as infile:
    HC = json.load(infile)

  return {
    'research_group': [
      'HC',
    ],
    'subject_folder': {
      'HC': HC,
    },
  }
