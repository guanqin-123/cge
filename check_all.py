from check_ce import ce_checker
from generate_df import GroundTruthTemplate, AllVerificationResults
import os
import z3
import numpy as np
import pandas as pd
from config import *
import time

class Solver:
    def __init__(self,verification_results_dir, benchmarks_dir):
        self.verification_results_dir = verification_results_dir
        self.benchmarks_dir = benchmarks_dir

        self.all_results_df = self.get_all_results_df()
        
        self.ground_truth_df = self.get_ground_truth_df()

        self.results_paths = AllVerificationResults(self.verification_results_dir, self.benchmarks_dir).result_paths

        self.result_dir = results_path


    def get_ground_truth_df(self):
        ground_truth_df = GroundTruthTemplate(self.verification_results_dir, self.benchmarks_dir)
        return ground_truth_df()

    def get_all_results_df(self):
        all_verification_results = AllVerificationResults(self.verification_results_dir, self.benchmarks_dir)
        # print(all_verification_results().to_string())
        return all_verification_results()




    def find_any_sat(self):
        # print(self.all_results_df.to_string())
        for index, row in self.all_results_df.iterrows():
            benchmark_name = row['benchmark']
            model_path = row['model_path']
            property_path = row['property_path']
            
            # check if there is a sat result from each verifier
            for verifier_result_column_name in self.all_results_df.columns[3:]:
                # print(row[verifier])
                verifier = verifier_result_column_name.split("_")[0]
                if row[verifier_result_column_name] == 'sat':
                    # print(f'Found a sat result for {benchmark_name} with verifier {verifier}')
                    model_name = model_path.split('/')[-1][:-5]
                    property_name = property_path.split('/')[-1][:-7]
                    ce_name = f'{model_name}_{property_name}.counterexample'
                    
                    ce_file_path = os.path.join(self.results_paths[verifier], benchmark_name, ce_name)
                    if not os.path.exists(ce_file_path):
                        # print(f'Counterexample not found for {benchmark_name} with verifier {verifier_result_column_name}')
                        # jump to next verifier
                        continue
                    result = ce_checker(ce_file_path, model_path, property_path)()
                    # print(result)
                    # write to the ground truth dataframe
                    if result==z3.sat:
                        self.ground_truth_df.loc[(self.ground_truth_df['benchmark']==benchmark_name) & (self.ground_truth_df['model_path']==model_path) & (self.ground_truth_df['property_path']==property_path), 'ground_truth'] = 'sat'
                        self.all_results_df.loc[(self.all_results_df['benchmark']==benchmark_name) & (self.all_results_df['model_path']==model_path) & (self.all_results_df['property_path']==property_path), f'{verifier}_true'] = 'correct'
                        
                        


    def get_and_compare_gt(self):
        for index, row in self.ground_truth_df.iterrows():
            row_keys = row.iloc[:3].values
            gt = row.iloc[3]

            matching_row = self.all_results_df[(self.all_results_df.iloc[:, :3] == row_keys).all(axis=1)]
            
            if gt == 'sat':
                for col in self.all_results_df.columns:
                    matching_index = matching_row.index[0]
                    if col.endswith('_result'):
                        verifier = col.split('_')[0]
                        verifier_true = verifier+'_true'
                        if verifier_true in matching_row.columns:
                            if self.all_results_df.at[matching_index, col] == 'sat':
                                self.all_results_df.at[matching_index, verifier_true] = 'correct'
                            if self.all_results_df.at[matching_index, col] == 'unsat':
                                self.all_results_df.at[matching_index, verifier_true] = 'wrong'
                        else:
                            raise ValueError (f'Column {verifier_true} not found in the all_results_df')
            else:
                for col in self.all_results_df.columns:
                    matching_index = matching_row.index[0]
                    if col.endswith('_result'):
                        if self.all_results_df.at[matching_index, col] == 'unsat':
                            self.ground_truth_df.at[index, 'ground_truth'] = 'unsat'


    def get_estimated_gt(self):
        for index, row in self.ground_truth_df.iterrows():
            row_keys = row.iloc[:3].values
            gt = row.iloc[3]

            matching_row = self.all_results_df[(self.all_results_df.iloc[:, :3] == row_keys).all(axis=1)]
            
            if gt == 'unsat':
                for col in self.all_results_df.columns:
                    matching_index = matching_row.index[0]
                    if col.endswith('_result'):
                        verifier = col.split('_')[0]
                        verifier_true = verifier+'_true'
                        if verifier_true in matching_row.columns:
                            if self.all_results_df.at[matching_index, col] == 'unsat':
                                self.all_results_df.at[matching_index, verifier_true] = 'correct'
                            if self.all_results_df.at[matching_index, col] == 'sat':
                                self.all_results_df.at[matching_index, verifier_true] = 'wrong'

    def pop_unknown_gt(self):
        self.chect_unclear_gt_exit()
        for index,row in self.ground_truth_df.iterrows():
            row_keys = row.iloc[:3].values
            gt = row.iloc[3]
            if pd.isna(gt):
                # write this row's value to unknown_gt.csv
                df_row = pd.DataFrame([row])
                df_row.to_csv(os.path.join(self.result_dir, 'unclear_gt.csv'), mode='a', index=False, header=False)
                self.ground_truth_df.drop(index, inplace=True)
                self.all_results_df.drop(self.all_results_df[(self.all_results_df.iloc[:, :3] == row_keys).all(axis=1)].index, inplace=True)
        self.write_to_csv(os.path.join(self.result_dir, 'cleaned_ground_truth.csv'), os.path.join(self.result_dir, 'cleaned_all_results.csv'))

        
    def write_to_csv(self, gt_path, all_results_path):
        self.ground_truth_df.to_csv(gt_path, index=False)
        self.all_results_df.to_csv(all_results_path, index=False)

    def chect_unclear_gt_exit(self):
        # if it is exit, then remove the unclear_gt.csv
        if os.path.exists(os.path.join(self.result_dir, 'unclear_gt.csv')):
            os.remove(os.path.join(self.result_dir, 'unclear_gt.csv'))

    def __call__(self):
        # create gt
        self.find_any_sat()
        # find gt for sat
        self.get_and_compare_gt()
        # estimate gt for unsat
        self.get_estimated_gt()
        self.write_to_csv(os.path.join(self.result_dir, 'ground_truth.csv'), os.path.join(self.result_dir, 'all_results.csv'))
        self.pop_unknown_gt()
        return self.ground_truth_df, self.all_results_df






if __name__ == "__main__":
    print('\n------------- Start running, check results at ./result ---------------\n')
    start_time = time.time()
    verification_results_dir = './verification_results'
    benchmarks_dir = './benchmarks'
    solver = Solver(verification_results_dir, benchmarks_dir)
    gt_df, all_results_df = solver()
    print(f'\n---------- Use:{time.time()- start_time} Seconds ---------\n')

        

