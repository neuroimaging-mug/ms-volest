import json

def get_research_groups():
  with open('BL.json', 'r') as infile:
    BL = json.load(infile)
  
  with open('FU.json', 'r') as infile:
    FU = json.load(infile)

  return {
    'research_group': [
      'BL',
      'FU',
    ],
    'subject_folder': {
      'BL': BL,
      'FU': FU,
    },
  }
