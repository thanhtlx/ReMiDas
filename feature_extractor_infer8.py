from variant_ensemble import *

if __name__ == '__main__':
    
    print("Inferring variant 8...")
    infer_variant_8('train', 'features/feature_variant_8_train.txt', need_feature_only=True)
    infer_variant_8('test_java', 'features/feature_variant_8_test_java.txt', need_feature_only=True)
    infer_variant_8(
        'val', 'features/feature_variant_8_val.txt', need_feature_only=True)
