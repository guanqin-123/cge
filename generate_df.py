import os
import pandas as pd
import csv


class AllVerificationResults:

    def __init__(self, verification_results_dir, benchmarks_dir):
        # "/home/feng/Documents/cge/verification_results"
        self.verification_results_dir = verification_results_dir
        # '/home/feng/Documents/cge/benchmarks'
        self.benchmarks_dir = benchmarks_dir

        # ['abcrown', 'debona', 'marabou', 'mip', 'mnbab', 'nnenum', 'peregrinn']
        self.verifier_names = self.get_verifier_names()


        # {'abcrown': '/home/feng/Documents/cge/verification_results/abcrown', 'debona': '/home/feng/Documents/cge/verification_results/debona', 'marabou': '/home/feng/Documents/cge/verification_results/marabou', 'mip': '/home/feng/Documents/cge/verification_results/mip', 'mnbab': '/home/feng/Documents/cge/verification_results/mnbab', 'nnenum': '/home/feng/Documents/cge/verification_results/nnenum', 'peregrinn': '/home/feng/Documents/cge/verification_results/peregrinn'}
        self.result_paths = self.get_verification_results_paths()

        # ['abcrown_result', 'abcrown_time', 'debona_result',  'debona_time', 'marabou_result', 'marabou_time','mip_result','mip_time','mnbab_result','mnbab_time','nnenum_result','nnenum_time', 'peregrinn_result','peregrinn_time']
        # ['benchmark', 'model_path', 'property_path', 'ground_truth']
        self.verification_results_headers, self.ground_truth_headers = self.generate_df_headers()

        # benchmark_names ['acasxu', 'collins_rul_cnn', 'mnist_fc', 'rl_benchmarks', 'tllverifybench', 'traffic_signs_recognition','vggnet16']
        # benchmark_paths {'acasxu': './benchmarks/acasxu', 'collins_rul_cnn': './benchmarks/collins_rul_cnn', 'mnist_fc': './benchmarks/mnist_fc', 'rl_benchmarks': './benchmarks/rl_benchmarks', 'tllverifybench': './benchmarks/tllverifybench', 'traffic_signs_recognition': './benchmarks/traffic_signs_recognition', 'vggnet16': './benchmarks/vggnet16'}
        self.benchmark_names, self.benchmark_paths = self.get_benchmark_names()

        self.all_results_df = self.generate_empty_results_df()


    def get_verifier_names(self)->list:
        subdirs = [name for name in os.listdir(self.verification_results_dir) if os.path.isdir(os.path.join(self.verification_results_dir, name))]
        subdirs.sort()
        # ['abcrown', 'debona', 'marabou', 'mip', 'mnbab', 'nnenum', 'peregrinn']
        return subdirs
    
    def get_verification_results_paths(self)->dict:
        # {'abcrown': '/home/feng/Documents/cge/verification_results/abcrown', 'debona': '/home/feng/Documents/cge/verification_results/debona', 'marabou': '/home/feng/Documents/cge/verification_results/marabou', 'mip': '/home/feng/Documents/cge/verification_results/mip', 'mnbab': '/home/feng/Documents/cge/verification_results/mnbab', 'nnenum': '/home/feng/Documents/cge/verification_results/nnenum', 'peregrinn': '/home/feng/Documents/cge/verification_results/peregrinn'}
        return {verifier: os.path.join(self.verification_results_dir, verifier) for verifier in self.verifier_names}
    
    def generate_df_headers(self):
        # return df headers for verification results and ground truth
        verifier_part = [ f'{verifier}_{i}' for verifier in self.verifier_names for i in ['result', 'time', 'true']]
        return ['benchmark', 'model_path', 'property_path']+verifier_part, ['benchmark', 'model_path', 'property_path', 'ground_truth']
    
    def get_benchmark_names(self):
        names = [name for name in os.listdir(self.benchmarks_dir) if os.path.isdir(os.path.join(self.benchmarks_dir, name))]
        names.sort()
        all_benchmark_paths = {name: os.path.join(self.benchmarks_dir, name) for name in names}
        return names, all_benchmark_paths
    
    def generate_empty_results_df(self):
        all_results_df = pd.DataFrame(columns=self.verification_results_headers)
        for benchmark_name in self.benchmark_paths:
            instance_file_path = os.path.join(self.benchmark_paths[benchmark_name],'instances.csv')
            with open(instance_file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    model = os.path.join(self.benchmark_paths[benchmark_name], row[0])
                    property = os.path.join(self.benchmark_paths[benchmark_name], row[1])
                    all_results_df.loc[len(all_results_df)] = {'benchmark': benchmark_name, 'model_path': model, 'property_path': property}
        return all_results_df
    
    def add_results_to_df(self):
        results_dirs = [(verifier, os.path.join(os.path.join(self.verification_results_dir, verifier),'results.csv')) for verifier in self.verifier_names]
        for verifier, results_dir in results_dirs:
            with open(results_dir, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    benchmark_name = row[0] 
                    if benchmark_name in self.benchmark_names:
                        model = row[1]
                        property = row[2]
                        if row[4]=='sat' or row[4]=='unsat':
                            verif_res = row[4]
                        else:
                            verif_res = 'unknown'
                        verif_time = row[5]
                        self.all_results_df.loc[(self.all_results_df['benchmark']==benchmark_name) & (self.all_results_df['model_path']==model) & (self.all_results_df['property_path']==property), f'{verifier}_result'] = verif_res
                        self.all_results_df.loc[(self.all_results_df['benchmark']==benchmark_name) & (self.all_results_df['model_path']==model) & (self.all_results_df['property_path']==property), f'{verifier}_time'] = verif_time
                    else:
                        raise ValueError(f'{benchmark_name} not in benchmark_names')
                    

    def __call__(self):
        self.add_results_to_df()
        return self.all_results_df
    

class GroundTruthTemplate(AllVerificationResults):

    def __init__(self, verification_results_dir, benchmarks_dir):
        super().__init__(verification_results_dir, benchmarks_dir)
        self.ground_truth_df = self.generate_gt_df()

    def generate_gt_df(self):
        # ['benchmark', 'model_path', 'property_path', 'ground_truth']
        gt_df = pd.DataFrame(columns=self.ground_truth_headers)
        for benchmark_name in self.benchmark_paths:
            instance_file_path = os.path.join(self.benchmark_paths[benchmark_name],'instances.csv')
            with open(instance_file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    model = os.path.join(self.benchmark_paths[benchmark_name], row[0])
                    property = os.path.join(self.benchmark_paths[benchmark_name], row[1])
                    gt_df.loc[len(gt_df)] = {'benchmark': benchmark_name, 'model_path': model, 'property_path': property}
        return gt_df
    
    def __call__(self):
        return self.ground_truth_df

        

        


if __name__ == "__main__":
    # test
    verification_results_dir = "./verification_results"
    benchmarks_dir = "./benchmarks"
    all_verification_results = AllVerificationResults(verification_results_dir, benchmarks_dir)
    # get the dataframe with all results
    print(all_verification_results().to_string())