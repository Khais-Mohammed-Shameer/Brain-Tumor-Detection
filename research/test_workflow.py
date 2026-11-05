import unittest
import numpy as np
from workflow import assert_independent, grouped_split, image_input, metrics
from pathlib import Path


class ResearchIntegrityTests(unittest.TestCase):
    def test_split_keeps_groups_together_and_is_reproducible(self):
        rows=[{'path':f'{i}-{j}.png','label':str(i%2),'group':f'patient-{i}','sha256':f'{i}-{j}'} for i in range(40) for j in range(2)]
        first,counts=grouped_split(rows,42);second,_=grouped_split(rows,42)
        self.assertEqual(first,second);assert_independent(first)
        self.assertTrue(all(min(count)>0 for count in counts.values()))
        self.assertEqual({r['split'] for r in first},{'train','validation','test'})

    def test_rejects_identical_images_assigned_to_different_groups(self):
        rows=[{'path':str(i),'label':'0','group':str(i),'sha256':'same'} for i in range(20)]
        with self.assertRaisesRegex(ValueError,'different group'):grouped_split(rows)

    def test_rejects_cross_split_group_and_duplicate_leakage(self):
        with self.assertRaisesRegex(ValueError,'leakage'):
            assert_independent([{'group':'same','sha256':'a','split':'train'},{'group':'same','sha256':'b','split':'test'}])
        with self.assertRaisesRegex(ValueError,'leakage'):
            assert_independent([{'group':'a','sha256':'same','split':'train'},{'group':'b','sha256':'same','split':'test'}])

    def test_metrics_with_known_false_positive_and_false_negative(self):
        result=metrics([0,0,1,1],[.1,.8,.4,.9])
        self.assertEqual(result['confusion_matrix'],{'tn':1,'fp':1,'fn':1,'tp':1})
        for key in ['accuracy','sensitivity','specificity','precision','f1']:self.assertEqual(result[key],.5)
        self.assertEqual(result['auroc'],.75)

    def test_quality_rejects_blank_noise_unreadable_and_tiny(self):
        for name in ['black.png','white.png','noise.png','invalid.png','tiny.png']:
            with self.subTest(name=name),self.assertRaises(ValueError):image_input(Path(__file__).parents[1]/'tests/fixtures'/name)

    def test_python_preprocessing_matches_frozen_tensor(self):
        root=Path(__file__).parents[1]
        actual=image_input(root/'public/samples/reference-tumor.jpg')
        expected=np.fromfile(root/'tests/reference-tumor.f32',dtype='<f4').reshape(240,240,3)
        np.testing.assert_array_equal(actual,expected)


if __name__=='__main__':unittest.main()
