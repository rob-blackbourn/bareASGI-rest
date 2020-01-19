from datetime import datetime, timedelta
import inspect
import json
import logging
from typing import Dict, List, Optional, Union
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict
from urllib.error import HTTPError

from bareasgi.basic_router.path_definition import PathDefinition

from bareasgi_rest.types import Body
from bareasgi_rest.swagger.entry import make_swagger_entry
from bareasgi_rest.arg_builder import make_args
from bareasgi_rest.protocol.json import from_json_value, from_json, to_json

Author = TypedDict(
    'Author',
    {
        '@type': str,
        'name': str
    },
    total=False
)

HowToTool = TypedDict(
    'HowToTool',
    {
        '@type': str,
        'name': str
    },
    total=False
)

Recipe = TypedDict(
    'Recipe',
    {
        '@context': str,
        '@type': str,
        'name': str,
        'author': Optional[Author],
        'description': Optional[str],
        'date_published': Optional[datetime],
        'image': str,
        'prep_time': Optional[timedelta],
        'cook_time': Optional[timedelta],
        'recipe_ingredient': List[str],
        'recipe_instructions': List[str],
        'recipe_category': Optional[str],
        'recipe_cuisine': Optional[str],
        'keywords': Optional[List[str]],
        'tool': Optional[List[HowToTool]],
        'foo': Optional[Union[str, int]]
    },
    total=False
)

recipe_json = """
{
  "@context": "http://schema.org/",
  "@type": "Recipe",
  "name": "Beef Empanada",
  "author": {
    "@type": "Person",
    "name": "Rob Blackbourn"
  },
  "description": "",
  "datePublished": "2019-02-15T19:59:57+00:00",
  "image": [
    "https://www.example.com/image.png"
  ],
  "prepTime": "PT10M",
  "cookTime": "PT15M",
  "recipeIngredient": [
    "4 onions chopped,2.5 kg empanada pastry,",
    "2 tsp salt,",
    "1 tbsp smoked paprika,",
    "1 tbsp chilli flakes,",
    "1 tbsp cumin,",
    "oregano,",
    "500g sirloin chopped into 1cm cubes.",
    "3 spring onions chopped,",
    "3 eggs - boiled and roughly chopped.",
    "Eggwash",
    "Black olives (optional)"
  ],
  "recipeInstructions": [
    "In a small saucepan bring 2 cups of water to the boil and add 1 tbsp salt and 4 tbsp lard.",
    " Once the lard has melted, let the liquid cool.",
    "Mix the liquid with 7 cups of plain flour and knead it till dry and a little hard.",
    "Roll out the dough and cut into 5 circles the size of side plates.",
    "Put the dough into the fridge to chill.",
    "Put some lard in a medium frying pan on a medium heat, add four chopped onions and fry till soft.",
    "Season with 2 tsp salt, 1 tbsp smoked paprika, 1 tbsp chilli flakes,  1 tbsp cumin.",
    "Empty the pan into a bowl.",
    "Add some more lard and sear 500g sirloin chopped into 1cm cubes.",
    "Add the meat to the bowl with the onions.",
    "Add to the mixture, 3 chopped spring onions, and 3 roughly chopped boiled eggs.",
    "Chill the mixture in the fridge.",
    "After the mixture is cooled fill the empanada with 2 tbsp per circle of patry.",
    "Bake them in the oven at 200C for 10-15 minutes."
  ],
  "recipeCategory": null,
  "recipeCuisine": "Argentina",
  "keywords": ["empanada"],
  "tool": [
    {
      "@type": "HowToTool",
      "name": "Parchment paper."
    }
  ],
  "foo": 1
}
"""


def recipe_roundtrip(
        recipe: Body[Recipe]
) -> Recipe:
    """Recipe round trip

    Args:
        recipe (Body[Recipe]): The recipe

    Returns:
        Recipe: A recipe
    """
    return recipe.value


recipe_roundtrip_swagger_entry = make_swagger_entry(
    'POST',
    PathDefinition('/recipe'),
    recipe_roundtrip,
    b'application/json',
    b'application/json',
    'multi',
    ['Books'],
    200,
    'OK'
)
print(recipe_roundtrip_swagger_entry)

a = json.loads(recipe_json)
b = from_json_value(a, Recipe)
recipe_dict = from_json(recipe_json, b'application/json', {})

args, kwargs = make_args(
    inspect.signature(recipe_roundtrip),
    {},
    {},
    recipe_dict,
    from_json_value
)

response = recipe_roundtrip(*args, **kwargs)
roundtrip = to_json(response)

print("Done")
