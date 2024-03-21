#!/usr/bin/python3

import pywikibot
site = pywikibot.Site()

def get_cat_items(cat_name, include_subcats=False, seen_subcats=None):

    if seen_subcats is None:
        seen_subcats = {cat_name}

    cat =  pywikibot.Category(site, cat_name)

    all_items = []
    for m in cat.members():
        title = m.title()
        if include_subcats and title.startswith("Category:"):
            subcat = title.removeprefix("Category:")
            if subcat not in seen_subcats:
                seen_subcats.add(subcat)
                all_items += get_cat_items(subcat, True, seen_subcats)
        else:
            all_items.append(title)

    return all_items

def main():
    import argparse
    argparser = argparse.ArgumentParser(description="Dump contents of a category")
    argparser.add_argument("cat", help="category to dump")
    argparser.add_argument("--subcats", help="include subcats", action='store_true')
    args = argparser.parse_args()


    #if args.dump_templates:
    #    dump_cat_templates("Definition_templates", args.dump_json)
    #    exit()


    for t in sorted(set(get_cat_items(args.cat, include_subcats=args.subcats))):
        print(t)

if __name__ == "__main__":
    main()
