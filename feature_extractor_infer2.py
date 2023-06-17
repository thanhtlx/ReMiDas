from variant_ensemble import *

if __name__ == '__main__':

    print("Inferring variant 2...")
    infer_variant_2(
        'val', 'features/feature_variant_2_val.txt', need_feature_only=True)
    infer_variant_2(
        'train', 'features/feature_variant_2_train.txt', need_feature_only=True)
    infer_variant_2(
        'test_java', 'features/feature_variant_2_test_java.txt', need_feature_only=True)
    print('-' * 64)
