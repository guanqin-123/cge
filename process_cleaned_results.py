import pandas as pd

import os
from config import benchmarks, deduct


class Solver:

    def __init__(self, cleaned_gt_path,cleaned_all_result_path,verification_results_dir, retain_rate=1):
        self.c_gt_path = cleaned_gt_path
        self.c_all_result_path = cleaned_all_result_path
        self.verification_results_dir = verification_results_dir
        self.benchmarks = benchmarks
        self.subdirs = self.get_subdirs()
        self.ground_truth_df, self.all_results_df = self.get_dfs()
        self.headers = ['verifier', 'TP', 'FP', 'TN', 'FN', 'soundness', 'completeness']
        self.detail_headers = ['verifier', 'benchmark', 'TP', 'FP', 'unknownFP','TN','FN', 'unknownFN']
        self.detail_table = self.init_detail_results_table()
        
        self.results_table = self.init_results_table()
        self.retain_rate = retain_rate

    def get_dfs(self):
        return pd.read_csv(self.c_gt_path), pd.read_csv(self.c_all_result_path)
    
    def init_detail_results_table(self):
        detail_table = pd.DataFrame(columns=self.detail_headers)
        for i in self.subdirs:
            for j in self.benchmarks:
                detail_table.loc[len(detail_table)] = [i, j, 0, 0, 0, 0, 0, 0]
        return detail_table
    
    def deduct_results_table(self):
        self.all_results_df = self.all_results_df.sample(frac=self.retain_rate)

    def deduct_all_results_df(self):
        for col in self.all_results_df.columns[3:]:
            verifier = col.split('_')[0]
            if verifier not in deduct:
                self.all_results_df.drop(columns=[col], inplace=True)


    def init_results_table(self):
        results_table = pd.DataFrame(columns=self.headers)
        for i in self.subdirs:
            results_table.loc[len(results_table)] = [i, 0, 0, 0, 0, 0, 0]
        return results_table
        
    def get_subdirs(self):
        subdirs = [name for name in os.listdir(self.verification_results_dir) if os.path.isdir(os.path.join(self.verification_results_dir, name))]
        subdirs.sort()
        return subdirs
    
    def detail_evaluate_all(self):
        for _, row in self.all_results_df.iterrows():
            row_keys = row.iloc[0:3].values
            for col in self.all_results_df.columns:
                if col =='benchmark':
                    benchmark = row[col]
                    if benchmark not in self.detail_table['benchmark'].values:
                        raise ValueError(f"Benchmark: {benchmark} not in detail results table!")
                if col.endswith('result'):
                    verifier = col.split('_')[0]

                    verification_result = row[col]

                    verdict = row[verifier+'_true']

                    if verifier not in self.detail_table['verifier'].values:
                        raise ValueError(f"Verifier: {verifier} not in detail results table!")
                    
                    idx = self.detail_table.index[(self.detail_table['verifier'] == verifier) & (self.detail_table['benchmark'] == benchmark)].tolist()[0]
                    if verification_result == 'unsat' and verdict == 'correct':
                        self.detail_table.at[idx, 'TP'] += 1

                    elif verification_result == 'unsat' and verdict == 'wrong':
                        self.detail_table.at[idx, 'FP'] += 1

                    elif verification_result == 'sat' and verdict == 'correct':
                        self.detail_table.at[idx, 'TN'] += 1

                    elif verification_result == 'sat' and verdict == 'wrong':
                        self.detail_table.at[idx, 'FN'] += 1

                    elif verification_result == 'unknown' or pd.isna(verification_result) or verification_result=='':
                        matching_row = self.ground_truth_df[(self.ground_truth_df.iloc[:,:3] == row_keys).all(axis=1)]
                        ground_truth = matching_row.iloc[0,3]
                        if ground_truth == 'unsat':
                            self.detail_table.at[idx, 'unknownFN'] += 1
                        elif ground_truth == 'sat':
                            self.detail_table.at[idx, 'unknownFP'] += 1
                        else:
                            raise ValueError(f"Ground truth: {ground_truth} not in ['unsat', 'sat']")
                    else:
                        raise ValueError(f"Verification result: {verification_result} not in ['unsat', 'sat', 'unknown']")
                
    
    
    def evaluate_all(self):
        for _, row in self.all_results_df.iterrows():
            row_keys = row.iloc[0:3].values
            for col in self.all_results_df.columns:
                if col.endswith('result'):
                    verifier = col.split('_')[0]
                    
                    # get the value of the cell
                    verification_result = row[col]

                    # get another column value
                    verdict = row[verifier + "_true"]

                    # check if the verifier in results_table verifier column
                    if verifier not in self.results_table['verifier'].values:
                        raise ValueError(f"Verifier: {verifier} not in results_table!")
                    
                    idx = self.results_table.index[self.results_table['verifier'] == verifier].tolist()[0]

                    # update the results_table
                    if verification_result == 'unsat' and verdict == 'correct':
                        self.results_table.at[idx, 'TP'] += 1

                    elif verification_result == 'unsat' and verdict == 'wrong':
                        self.results_table.at[idx, 'FP'] += 1

                    elif verification_result == 'sat' and verdict == 'correct':
                        self.results_table.at[idx, 'TN'] += 1

                    elif verification_result == 'sat' and verdict == 'wrong':
                        self.results_table.at[idx, 'FN'] += 1

                    elif verification_result == 'unknown' or pd.isna(verification_result) or verification_result=='':
                        # get the ground truth from gt dataframe
                        matching_row = self.ground_truth_df[(self.ground_truth_df.iloc[:,:3]==row_keys).all(axis=1)]
                        # get the value of the 4th column
                        ground_truth= matching_row.iloc[0,3]
                        if ground_truth == 'unsat':
                            self.results_table.at[idx, 'FN'] += 1
                        elif ground_truth == 'sat':
                            self.results_table.at[idx, 'FP'] += 1

    def evaluate_known(self):
        for _, row in self.all_results_df.iterrows():
            # row_keys = row.iloc[0:3].values
            for col in self.all_results_df.columns:
                if col.endswith('result'):
                    verifier = col.split('_')[0]
                    
                    # get the value of the cell
                    verification_result = row[col]

                    # get another column value
                    verdict = row[verifier + "_true"]

                    # check if the verifier in results_table verifier column
                    if verifier not in self.results_table['verifier'].values:
                        raise ValueError(f"Verifier: {verifier} not in results_table!")
                    
                    idx = self.results_table.index[self.results_table['verifier'] == verifier].tolist()[0]

                    # update the results_table
                    if verification_result == 'unsat' and verdict == 'correct':
                        self.results_table.at[idx, 'TP'] += 1

                    elif verification_result == 'unsat' and verdict == 'wrong':
                        self.results_table.at[idx, 'FP'] += 1

                    elif verification_result == 'sat' and verdict == 'correct':
                        self.results_table.at[idx, 'TN'] += 1

                    elif verification_result == 'sat' and verdict == 'wrong':
                        self.results_table.at[idx, 'FN'] += 1


    def evaluate_unknown(self):
        for _, row in self.all_results_df.iterrows():
            row_keys = row.iloc[0:3].values
            for col in self.all_results_df.columns:
                if col.endswith('result'):
                    verifier = col.split('_')[0]
                    
                    # get the value of the cell
                    verification_result = row[col]

                    # get another column value
                    verdict = row[verifier + "_true"]

                    # check if the verifier in results_table verifier column
                    if verifier not in self.results_table['verifier'].values:
                        raise ValueError(f"Verifier: {verifier} not in results_table!")
                    
                    idx = self.results_table.index[self.results_table['verifier'] == verifier].tolist()[0]

                    # update the results_table
                    if verification_result == 'unknown' or pd.isna(verification_result) or verification_result=='':
                        # get the ground truth from gt dataframe
                        matching_row = self.ground_truth_df[(self.ground_truth_df.iloc[:,:3]==row_keys).all(axis=1)]
                        # get the value of the 4th column
                        ground_truth= matching_row.iloc[0,3]
                        if ground_truth == 'unsat':
                            self.results_table.at[idx, 'FN'] += 1
                        elif ground_truth == 'sat':
                            self.results_table.at[idx, 'FP'] += 1

    def get_soundness_completeness(self):
        for index, row in self.results_table.iterrows():
            TP = row['TP']
            FP = row['FP']
            TN = row['TN']
            FN = row['FN']
            if TP+FP == 0:
                soundness = 0
            else:
                soundness = TP/(TP+FP)
            if TN+FN == 0:
                completeness=0
            else:
                completeness = TN/(TN+FN)
            self.results_table.at[index, 'soundness'] = soundness
            self.results_table.at[index, 'completeness'] = completeness

    def to_latex_table(self):
        pass

    def get_score(self):
        # get the 'verifier' colomn of the results_table
        verifiers = self.results_table['verifier'].values
        # get the 'soundness' column of the results_table
        soundness = self.results_table['soundness'].values
        # get the 'completeness' column of the results_table
        completeness = self.results_table['completeness'].values
        # calculate the score
        score = 2/(1/soundness + 1/completeness)
        # create a new dataframe
        score_df = pd.DataFrame({'verifier':verifiers, 'score':score})
        return score_df


    def __call__(self, mode):
        if mode == 'all':
            self.evaluate_all()
            self.get_soundness_completeness()

        elif mode == 'known':
            self.evaluate_known()
            self.get_soundness_completeness()

        elif mode == 'unknown':
            self.evaluate_unknown()
            # self.get_soundness_completeness()

        elif mode == 'detail':
            self.detail_evaluate_all()
            # self.get_soundness_completeness
        elif mode == 'retain':
            self.deduct_results_table()
            self.evaluate_all()
            self.get_soundness_completeness()
        elif mode == 'deduct':
            self.deduct_all_results_df()
            self.evaluate_all()
            self.get_soundness_completeness()
        elif mode == 'score':
            self.evaluate_all()
            self.get_soundness_completeness()
            return self.get_score()
        else:
            raise ValueError(f"Invalid mode: {mode}")







if __name__ == '__main__':
    cleaned_gt_path = '/home/feng/Documents/cge/results/cleaned_ground_truth.csv'
    cleaned_all_result_path = '/home/feng/Documents/cge/results/cleaned_all_results.csv'
    verification_results_dir="/home/feng/Documents/cge/verification_results"
    benchmark_dir = '/home/feng/Documents/cge/benchmarks'
    solver = Solver(cleaned_gt_path,cleaned_all_result_path,verification_results_dir)
    # print(solver.results_table.to_string())
    solver('all')
    print(solver.results_table.to_string())