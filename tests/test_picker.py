# Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
import json
import unittest
from unittest.mock import Mock, patch

from amplia_picker import NativePicker


class NativePickerTests(unittest.TestCase):
    def picker(self, output, code=0, folder=False):
        process=Mock(); process.communicate.return_value=(output,''); process.returncode=code
        with patch('amplia_picker.subprocess.Popen',return_value=process) as popen, \
             patch('amplia_picker.threading.Thread'):
            picker=NativePicker('C:/Pasta com espaço/acentuação',folder=folder)
        return picker,process,popen.call_args

    def test_path_is_passed_as_an_argument_without_shell(self):
        picker,process,call=self.picker(json.dumps({'caminho':'C:/pasta/imagem.png'}))
        self.assertIn('C:/Pasta com espaço/acentuação',call.args[0])
        self.assertNotIn('shell',call.kwargs)
        self.assertIsNone(picker.poll())
        picker.collect()
        self.assertEqual(picker.poll(),{'caminho':'C:/pasta/imagem.png','erro':None})

    def test_cancel_is_a_result_and_folder_has_its_own_mode(self):
        picker,process,call=self.picker('{"caminho":null}',folder=True)
        self.assertIn('--folder',call.args[0])
        picker.collect()
        self.assertEqual(picker.poll(),{'caminho':None,'erro':None})

    def test_broken_response_is_reported(self):
        for value in ('sem JSON','[]','{"caminho":true}','{"erro":"falhou"}'):
            with self.subTest(value=value):
                picker,_process,_call=self.picker(value)
                picker.collect()
                self.assertTrue(picker.poll()['erro'])

    def test_cancel_only_terminates_its_own_pending_process(self):
        picker,process,_call=self.picker('{"caminho":null}')
        process.poll.return_value=None
        picker.cancel();process.terminate.assert_called_once()
        process.reset_mock();process.poll.return_value=0
        picker.cancel();process.terminate.assert_not_called()


if __name__=='__main__':
    unittest.main(verbosity=2)
