from variant_ensemble import *

if __name__ == '__main__':
    print("Inferring variant 1...")
    infer_variant_1(
        'train', 'features/feature_variant_1_train.txt', need_feature_only=True)
    infer_variant_1(
        'test_java', 'features/feature_variant_1_test_java.txt', need_feature_only=True)
    infer_variant_1(
        'val', 'features/feature_variant_1_val.txt', need_feature_only=True)
    print('-' * 64)
