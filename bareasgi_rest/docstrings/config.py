"""Config"""


class Config:

    def __init__(self) -> None:
        self.napoleon_google_docstring = True
        self.napoleon_numpy_docstring = True
        self.napoleon_include_init_with_doc = False
        self.napoleon_include_private_with_doc = False
        self.napoleon_include_special_with_doc = False
        self.napoleon_use_admonition_for_examples = False
        self.napoleon_use_admonition_for_notes = False
        self.napoleon_use_admonition_for_references = False
        self.napoleon_use_ivar = False
        self.napoleon_use_param = True
        self.napoleon_use_rtype = True
        self.napoleon_use_keyword = True
        self.napoleon_custom_sections = None
