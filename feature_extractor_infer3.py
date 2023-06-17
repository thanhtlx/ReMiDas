from variant_ensemble import *

if __name__ == '__main__':

    print("Inferring variant 3...")
    infer_variant_3(
        'train', 'features/feature_variant_3_train.txt', need_feature_only=True)
    infer_variant_3(
        'test_java', 'features/feature_variant_3_test_java.txt', need_feature_only=True)
    infer_variant_3(
        'val', 'features/feature_variant_3_val.txt', need_feature_only=True)
