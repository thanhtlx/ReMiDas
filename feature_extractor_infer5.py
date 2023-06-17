from variant_ensemble import *

if __name__ == '__main__':

    print("Inferring variant 5...")
    infer_variant_5(
        'train', 'features/feature_variant_5_train.txt', need_feature_only=True)
    infer_variant_5(
        'test_java', 'features/feature_variant_5_test_java.txt', need_feature_only=True)
    infer_variant_5(
        'val', 'features/feature_variant_5_val.txt', need_feature_only=True)
    print('-' * 64)
