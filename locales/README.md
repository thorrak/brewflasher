

To extract strings, run `pip install pybabel` and then run the following command to regenerate `brewflasher.po`:
    `pybabel extract Main.py -o locales/brewflasher.po`

To compile strings (after updating), run:
    `python compile_languages.py locales`

