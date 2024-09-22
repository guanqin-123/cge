
from typing import Any
import numpy as np
import onnxruntime
import z3


class ce_checker:

    def __init__(self, ce_file_path, model_path, property_path) -> None:
        self.ce_file_path = ce_file_path
        self.model_path = model_path
        self.property_file_path = property_path

        self.ce_input = self.get_ce_input()
        self.output_properties = self.get_output_properties()
        
        self.network_output = self.get_network_output()
        pass

    def get_ce_input(self) -> list:
        # Read the counterexample file and return the input values of the counterexample
        with open(self.ce_file_path, 'r') as f:
            content = f.readlines()
            ce_input = list()

        for line in content:
            if "X" in line: 
                line = line.replace("(", "").replace(")","").replace(",", "").replace("\n", "")
                value = line.split()[-1]
                ce_input.append(float(value))
        f.close()
        return ce_input
    
    def get_network_output(self) -> list:
        # Get the output of the network for the given input
        input_vector = np.array(self.ce_input, dtype=np.float32)
        # print(input_vector.shape)
        sess = onnxruntime.InferenceSession(self.model_path)
        input_name = sess.get_inputs()[0].name
        input_shape = sess.get_inputs()[0].shape
        # print(input_shape)

        for i in range(len(input_shape)):
            if not isinstance(input_shape[i],int):
                input_shape[i]=1
        
        try: 
            input_data = input_vector.reshape(input_shape)
        except ValueError as e:
            # print(f"Input data shape {input_vector.shape} does not match model input shape {input_shape}")
            return 'error'
        if input_data.shape != tuple(input_shape):
            raise ValueError(f"Input data shape {input_data.shape} does not match model input shape {input_shape}")
        
        outputs = sess.run(None, {input_name: input_data})
        output = outputs[0]
        # print(output.flatten())
        return output.flatten()
    
    def get_output_properties(self) -> str:
        # Read the property file and return the output properties
        with open(self.property_file_path, 'r') as f:
            content = f.readlines()
        output_properties = ' '
        flag = False
        for line in content:
            if "Y" in line and "declare" in line:
                output_properties += line 
                # Unsafe -> acasxu; 
            elif "Output" in line or "output constraints" in line or "unsafe" in line or "coc" in line or "Unsafe" in line or 'strong left should be minimal' in line or "COC" in line:
                flag = True
            elif 'Input' in line or 'input constraints' in line or 'Input constraints' in line or 'input' in line or 'Input' in line:
                flag = False
            elif flag:
                output_properties += line
        f.close()
        # print(output_properties)
        return output_properties
    

    def reason(self) -> bool:
        # Reason about the output properties and the network output
        collectY_network_list = list()
        print(self.network_output)
        if self.network_output=='error':
            return z3.unsat
        for i in range(len(self.network_output)):
            single_value = self.network_output[i]
            if 'e' in str(single_value):
                r_value = str(single_value).split('e')[0]
                res = int(str(single_value).split("e")[1])
                collectY_network_list.append("(assert (= Y_{} (* {} (^ 10 {}))))".format(i, float(r_value), res))
            else:
                collectY_network_list.append("(assert (= Y_{} {}))".format(i, single_value))
        
        collectY_network_output_constraint = "".join(collectY_network_list)
        combine = self.output_properties + collectY_network_output_constraint
        combine = combine.replace("\n", "").encode(encoding='utf-8')
        solver = z3.Solver()
        solver.reset()
        try:
            SMT_properties = z3.parse_smt2_string(combine)
            solver.add(SMT_properties)
        except z3.Z3Exception:
            print(f"Error {combine}")
        return solver.check()
    
    def __call__(self) -> Any:
        return self.reason()
    


if __name__ == "__main__":
    # ce_file_path = "/home/feng/Documents/cge/verification_results/abcrown/traffic_signs_recognition/3_30_30_QConv_16_3_QConv_32_2_Dense_43_ep_30_model_30_idx_7040_eps_1.00000.counterexample"
    # model_path = './benchmarks/traffic_signs_recognition/onnx/3_30_30_QConv_16_3_QConv_32_2_Dense_43_ep_30.onnx'
    # property_path = './benchmarks/traffic_signs_recognition/vnnlib/model_30_idx_7040_eps_1.00000.vnnlib'
    ce_file_path ='/home/feng/Documents/cge2/old_results/test/s.counterexample'
    # ce_file_path = "/home/feng/Documents/cge/verification_results/marabou0/acasxu/ACASXU_run2a_1_2_batch_2000_prop_2.counterexample"
    # model_path = '/home/feng/Documents/cge/benchmarks/acasxu/onnx/ACASXU_run2a_1_2_batch_2000.onnx'
    model_path = '/home/feng/Documents/cge2/old_results/test/cifar_base_kw.onnx'
    # property_path = '/home/feng/Documents/cge/benchmarks/acasxu/vnnlib/prop_2.vnnlib'
    property_path = '/home/feng/Documents/cge2/old_results/test/cifar_base_kw-img1244-eps0.01568627450980392.vnnlib'
    ce = ce_checker(ce_file_path, model_path, property_path)
    print(ce())


