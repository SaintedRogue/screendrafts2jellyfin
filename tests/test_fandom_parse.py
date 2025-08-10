from screendraft2jellyfin.fandom import extract_ranked_films

WIKI = '''
The following films were drafted:

7. [[I Declare War]] by [[Billy Ray]]
<s>6. [[Harry Potter and the Goblet of Fire]] by [[Billy]]</s> vetoed by [[Graham]]
6. [[Harry Potter and the Prisoner of Azkaban]] by [[Billy Ray]]
5. [[E.T. the Extra-Terrestrial]] by [[Graham]]
4. [[Stand by Me]] by [[Billy Ray]]
<s>3. [[The Sandlot]] by [[Graham]]</s> removed via [[Commissioner Override]]
3. [[The Monster Squad]] by [[Graham]]
2. [[The Goonies]] by [[Billy Ray]]
1. [[Honey, I Shrunk the Kids]] by [[Graham]]
'''

def test_extract_ranked_films():
    films = extract_ranked_films(WIKI)
    titles = [f["title"] for f in films]
    assert "Harry Potter and the Goblet of Fire" not in titles
    assert titles[0] == "I Declare War"
    assert titles[-1] == "Honey, I Shrunk the Kids"
