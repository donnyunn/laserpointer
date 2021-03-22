import os.path
import billiard_submain
import time

folder_directory = os.path.dirname(os.path.abspath(__file__)) + '/resources/'
file_1_directory = folder_directory + '1'
while True:
    if os.path.isfile(file_1_directory) == True:
        billiard_submain.submain_func()
        print()
    time.sleep(1)


