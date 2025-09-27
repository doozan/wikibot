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
    if page.text != "{{auto cat}}":
        print("UNHANDLED TEXT (should be {{auto cat}})", category_name, [page.text])
        return

    page.text = "{{d|empty category, no longer needed}}"
    page.save("empty category, no longer needed")

def main():
    gp_cat = pywikibot.Category(site, 'Category:Pages using invalid parameters when calling templates')

    empty_cats = []
    count = 0

    print("XX")

    p_total =  gp_cat.categoryinfo["subcats"]
    for p_idx, p_cat in enumerate(gp_cat.subcategories(), 1):
#        p_cat = pywikibot.Category(site, 'Category:Pages using bad params when calling Greek templates')
        c_total =  p_cat.categoryinfo["subcats"]
        for c_idx, c_cat in enumerate(p_cat.subcategories(), 1):
            count += 1

            has_subcats = any(c_cat.subcategories())
            if has_subcats:
                print("has_subcats:", c_cat.title())

            page_count = len(list(p for p in c_cat.articles() if "Talk:" not in p.title() and "User:" not in p.title()))
            if page_count > 100:
                print(page_count, c_cat.title().ljust(120))

            if has_subcats or page_count:
                print(f"{count} {p_idx}/{p_total} {c_idx}/{c_total} {str(p_cat).ljust(64)}", end = '\r', file=sys.stderr)
                continue

            print("empty:", list(c_cat.articles()), c_cat.title())

            empty_cats.append(c_cat.title())
            m = re.search("^Category:Pages using invalid parameters when calling (Template:.*)", c_cat.title())
            if not m:
                print("NO MATCH", c_cat.title())
                continue
            template_name = m.group(1)
            if not replace_warn_with_error(template_name):
                print(f"Unable to auto-fix {template_name}")
                continue
            remove_category(c_cat.title())


if __name__ == "__main__":
    main()
