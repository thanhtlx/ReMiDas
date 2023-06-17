from variant_ensemble import *

if __name__ == '__main__':

    print("Inferring variant 7...")
    infer_variant_7(
        'train', 'features/feature_variant_7_train.txt', need_feature_only=True)
    infer_variant_7(
        'test_java', 'features/feature_variant_7_test_java.txt', need_feature_only=True)
    infer_variant_7(
        'val', 'features/feature_variant_7_val.txt', need_feature_only=True)
