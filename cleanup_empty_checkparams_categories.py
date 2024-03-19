#!/usr/bin/python3

import pywikibot
import re
import sys

site = pywikibot.Site("en", "wiktionary")

def replace_warn_with_error(template_name):
    page = pywikibot.Page(site, template_name)
    page_text = page.text

    new_text = page_text.replace("#invoke:checkparams|warn", "#invoke:checkparams|error")
    if new_text != page_text:
        page.text = new_text
        page.save("no existing calls with bad parameters, throw error instead of warning to avoid future misuse")

    return "#invoke:checkparams|error" in page.text

def remove_category(category_name):
    page = pywikibot.Page(site, category_name)
    assert page.text == "{{auto cat}}"
    page.text = "{{d|empty category, no longer needed}}"
    page.save("empty category, no longer needed")

def main():
    gp_cat = pywikibot.Category(site, 'Category:Pages using bad params when calling a template')

    empty_cats = []
    count = 0

    p_total =  gp_cat.categoryinfo["subcats"]
    for p_idx, p_cat in enumerate(gp_cat.subcategories(), 1):
        c_total =  p_cat.categoryinfo["subcats"]
        for c_idx, c_cat in enumerate(p_cat.subcategories(), 1):
            count += 1
            c_cat_is_empty = not any(p for p in c_cat.articles() if "Talk:" not in p.title() and "User:" not in p.title())
            print(f"{count} {p_idx}/{p_total} {c_idx}/{c_total} ({len(empty_cats)} empty)", end = '\r', file=sys.stderr)
            if c_cat_is_empty:
                print("empty:", list(c_cat.articles()), c_cat.title())
                empty_cats.append(c_cat.title())
                template_name = re.search("^Category:Pages using bad params when calling (Template:.*)", c_cat.title()).group(1)
                if not replace_warn_with_error(template_name):
                    print(f"Unable to auto-fix {template_name}")
                    continue
                remove_category(c_cat.title())


if __name__ == "__main__":
    main()
