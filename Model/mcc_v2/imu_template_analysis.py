from __future__ import division
import matplotlib
from scipy import signal
import numpy as np
import os
import sys
import pandas as pd
from datetime import date, datetime

from sklearn.metrics import classification_report, confusion_matrix
import timeit
import pickle
from pathlib import Path

from util_data import load_preprocessed_synced_imu, load_synced_imu_label, list_files, \
                      load_highdataquality_synced_imu_label, save_llist_as_txt, load_predictions, \
                      gt_df2list, recursive_merge, extract_filtered_acc_from_df, starttimes2segments, \
                      extend_interval_sec
from util_eval import event_evaluation, Averager
from util_plot import plt_imu_acc
from settings_seated import cough_names, cough_sessions, noncough_names, noncough_sessions, \
    all_subjects
import itertools
import matplotlib.pyplot as plt; plt.rcdefaults()
import matplotlib.pyplot as plt


def str_list_to_int_list(match_str):
    out_list = []
    for m in match_str:
        if len(m) > 0:
            out_list.append(int(m))
    return out_list


def get_templates_per_cough(result_id):
    sr_imu = 50
    l_template = 20
    
    total_coughs = 0

    hit_template_all_coughs = []
    for subject in all_subjects:
        # print(subject)
        for sess, name in zip(cough_sessions+noncough_sessions, cough_names+noncough_names):
            # print(subject, name)
            # ============================================================================= 
            #                                   matching
            # =============================================================================
            effect_save_name = "results/effect_templates_"+subject+"_"+name.replace("/", "_")+ \
                    result_id+".csv"
            match_df = pd.read_csv(effect_save_name)
            match_df['templates'] = match_df.templates.apply(lambda x: x[1:-1].split(','))

            # ============================================================================= 
            #                                      label
            # =============================================================================
            if sess in cough_sessions:
                # --------------------- can load diff types of labels
                # imu_gt = load_synced_imu_label(subject, sess)
                imu_gt = load_highdataquality_synced_imu_label(subject, sess)
            else:
                imu_gt = pd.DataFrame(columns = ['start' , 'end', 'label'])

            imu_gt['start'] = imu_gt['start'] * sr_imu
            imu_gt['end'] = imu_gt['end'] * sr_imu
            imu_gt_sec_list = gt_df2list(imu_gt)

            total_coughs += len(imu_gt)


            for start, end in imu_gt_sec_list:
                start = int(start // 5 * 5)
                end = int((end // 5 + 1) * 5)
                hit_template_cough = []

                moving_start = start
                moving_end = start + l_template

                if int(moving_start//5) < len(match_df):
                    match_str = match_df["templates"].iloc[int(moving_start//5)]
                    hit_template_cough += str_list_to_int_list(match_str)

                    while moving_end < end:
                        moving_start += 5
                        moving_end += 5
                        if int(moving_start//5) < len(match_df):
                            match_str = match_df["templates"].iloc[int(moving_start//5)]
                            hit_template_cough += str_list_to_int_list(match_str)

                if len(set(hit_template_cough)):
                    hit_template_all_coughs.append(list(set(hit_template_cough)))

    print(total_coughs)
    return hit_template_all_coughs


def convert_templates_per_cough_to_coughs_per_template(template_all_coughs):
    num_templates = 0
    for hit_template_this_cough in template_all_coughs:
        for hit_temp in hit_template_this_cough:
            if hit_temp > num_templates:
                num_templates = hit_temp
    num_templates += 1

    dic = {}
    for i in range(num_templates):
        dic[i] = []

    for i, hit_template_this_cough in enumerate(template_all_coughs):
        for hit_temp in hit_template_this_cough:
            dic[hit_temp].append(i)

    return dic


def plot_bar(lst):
    objects = list(range(len(lst)))
    y_pos = np.arange(len(objects))
    performance = lst

    plt.barh(y_pos, performance, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    # plt.xlabel('Usage')
    # plt.title('Programming language usage')
    plt.show()


def get_total_num_coughs(dic):
    max_cough_ind = 0
    for i in dic:
        for j in dic[i]:
            if j > max_cough_ind:
                max_cough_ind = j
    print(max_cough_ind)
    return max_cough_ind+1


def flat_lst(llst):
    flat_list = [item for sublist in llst for item in sublist]
    return flat_list


def select_template_covers_the_most(coughs, dic):
    most_covered_coughs_num = 0
    best_template_ind = 0
    for i in dic:
        num_covered = 0
        for k in dic[i]:
            if k in coughs:
                num_covered += 1
        if num_covered > most_covered_coughs_num:
            most_covered_coughs_num = num_covered
            best_template_ind = i
    print(best_template_ind)
    print(most_covered_coughs_num)
    left_coughs = coughs.copy()
    for k in dic[best_template_ind]:
        if k in left_coughs:
            left_coughs.remove(k)
    return best_template_ind, left_coughs
    

def rank_plot_dict(dic):    
    lst = [len(dic[i]) for i in dic]
    for i in range(len(lst)):
        if lst[i] > 250:
            print(i)
    print("\n\n")
    for i in range(len(lst)):
        if lst[i] > 390:
            print(i)
    
    lst = sorted(lst)
    plot_bar(lst)


def hitting_set_greedy(dic):
    all_coughs = list(range(get_total_num_coughs(dic)))
    left_coughs = all_coughs.copy()
    sel_templates = []
    for i in range(20):
        best_template_ind, left_coughs = select_template_covers_the_most(left_coughs, dic)
        sel_templates.append(best_template_ind)
    print(len(left_coughs))
    print(sel_templates)



if __name__ == '__main__':

    result_id = '07192'
    template_all_coughs = get_templates_per_cough(result_id)
    dic = convert_templates_per_cough_to_coughs_per_template(template_all_coughs)
    
    hitting_set_greedy(dic)
    # rank_plot_dict(dic)


