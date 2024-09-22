import os


# path to the results directory
results_path = './results'  
# git ignore the results directory, so create a new loacally
if not os.path.exists(results_path):
    os.makedirs(results_path)


benchmarks = ['acasxu','collins_rul_cnn', 'mnist_fc', 'rl_benchmarks', 'tllverifybench', 'traffic_signs_recognition','vggnet16']


deduct = ['abcrown','debona','marabou','marabou0','mip','mnbab']
# deduct = ['abcrown','debona','marabou','marabou0','mnbab','nnenum']