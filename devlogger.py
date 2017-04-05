#!/usr/bin/python

import os
import sys
import time
import argparse

def devlog(text):
    folder_path = os.path.join(os.path.expanduser('~'), 'devlogs')
    day_str = time.strftime("%A_%b%d_%Y")
    time_str = time.strftime("%I:%M %p")
    fn = '%s/%s.txt' % (folder_path, day_str)

    max_len = 69
    text_sections = []

    if len(text) <= max_len:
        text_sections = [text]
    else:
        words = text.split()
        while len(words):
            for i in range(len(words)):
                if len(' '.join(words[:i+1])) > max_len:
                    ind = i
                    break
            text_sections.append(' '.join(words[:ind]))
            words = words[ind:]

    final_text = '%s - %s\n' % (time_str, text_sections[0])

    if len(text_sections) > 1:
        final_text = '%s%s\n' % (final_text, '\n'.join(["%s%s" % ('           ', section) for section in text_sections[1:]]))

    if not os.path.isdir(folder_path):
        os.mk_dir(folder_path)

    with open(fn, 'a') as f:
       f.write(final_text)
