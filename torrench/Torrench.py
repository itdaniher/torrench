import platform
import os
import sys
import argparse
import torrench.utilities.check_config as check_config

__version__ = "Torrench (1.0.42)"

if platform.system() == 'Windows':

    from multiprocessing import Queue
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 3)
    os.system("mode CON: COLS=180 LINES=350") 	# Expand windows console window so output does not overlap (font==default).


def args():
    parser = argparse.ArgumentParser(description="Command-line torrent search tool.")
    parser.add_argument("-d", "--distrowatch", action="store_true", help="Search distrowatch")
    parser.add_argument("-t", "--thepiratebay", action="store_true", help="Search thepiratebay (TPB)")
    parser.add_argument("-k", "--kickasstorrent", action="store_true", help="Search KickassTorrent (KAT)")
    parser.add_argument("-m", "--all_magnets", action="store_true", help="Search KAT and TPB for all magnets.")
    parser.add_argument("search", help="Enter search string", nargs="?", default=None)
    parser.add_argument("-p", "--page-limit", type=int, help="Number of pages to fetch results from (1 page = 30 results).\n [default: 1]", default=1, dest="limit")
    parser.add_argument("-c", "--clear-html", action="store_true", default=False, help="Clear all [TPB] torrent description HTML files and exit.")
    parser.add_argument("-v", "--version", action='version', version=__version__, help="Display version and exit.")
    args = parser.parse_args()
    main(args)


def remove_temp_files():
    home = os.path.expanduser(os.path.join('~', '.torrench'))
    temp_dir = os.path.join(home, "temp")
    try:
        files = os.listdir(temp_dir)
    except FileNotFoundError:
        print("Directory not initialised.")
        sys.exit(2)
    if not files:
        print("\nNothing to remove\n")
        sys.exit(2)
    else:
        for count, file_name in enumerate(files, 1):
            os.remove(os.path.join(temp_dir, file_name))
        print("\nRemoved {} file(s).\n".format(count))
        sys.exit(2)


def torrent_fetch(args):
    input_title = args.search
    page_limit = args.limit
    if args.thepiratebay or args.kickasstorrent:
        if not check_config.file_exists():
            print("\nConfig file not configured. Configure to continue. Read docs for more info.\n")
            sys.exit(2)
        else:
            if args.thepiratebay:
                import torrench.modules.thepiratebay as tpb
                tpb.main(input_title, page_limit)

            elif args.kickasstorrent:
                import torrench.modules.kickasstorrent as kat
                kat.main(input_title, page_limit)

    elif args.distrowatch:
        import torrench.modules.distrowatch as distrowatch
        distrowatch.main(input_title)
    elif args.all_magnets:
        magnets = []
        from torrench.modules import thepiratebay, kickasstorrent
        for tracker in [kickasstorrent, thepiratebay]:
            proxy_list = tracker.proxy_select()
            url = tracker.cycle_proxies(proxy_list)
            output = tracker.get_results(url, input_title, page_limit)
            for result in tracker.mapper[1::]:
                magnets.append(result[1])
        for magnet in magnets:
            print(magnet)
    else:
        import torrench.modules.linuxtracker as linuxtracker
        linuxtracker.main(input_title)

def main(args):
    input_title = args.search
    page_limit = args.limit
    if args.clear_html:
        if args.thepiratebay:
            remove_temp_files()
        else:
            print("error: use -c with -t ")
            sys.exit(2)

    if input_title == None:
        print("\nInput string expected.\nUse --help for more\n")
        sys.exit(2)

    elif page_limit <= 0 or page_limit > 50:
        print("Enter valid page input [0<p<=50]")
        sys.exit(2)

    else:
        torrent_fetch(args)


if __name__ == "__main__":
    args()
