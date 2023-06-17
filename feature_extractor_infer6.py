from variant_ensemble import *

if __name__ == '__main__':
    print("Inferring variant 6...")
    infer_variant_6(
        'val', 'features/feature_variant_6_val.txt', need_feature_only=True)

    infer_variant_6(
        'train', 'features/feature_variant_6_train.txt', need_feature_only=True)
    infer_variant_6(
        'test_java', 'features/feature_variant_6_test_java.txt', need_feature_only=True)
