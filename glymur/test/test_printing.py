# -*- coding:  utf-8 -*-
"""Test suite for printing.
"""
# C0302:  don't care too much about having too many lines in a test module
# pylint: disable=C0302

# E061:  unittest.mock introduced in 3.3 (python-2.7/pylint issue)
# pylint: disable=E0611,F0401

# R0904:  Not too many methods in unittest.
# pylint: disable=R0904

import os
import struct
import sys
import tempfile
import warnings
import unittest

if sys.hexversion < 0x03000000:
    from StringIO import StringIO
else:
    from io import StringIO

if sys.hexversion <= 0x03030000:
    from mock import patch
else:
    from unittest.mock import patch

import lxml.etree as ET

import glymur
from glymur import Jp2k
from . import fixtures
from .fixtures import OPJ_DATA_ROOT, opj_data_file
from .fixtures import text_gbr_27, text_gbr_33, text_gbr_34


@unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
class TestPrinting(unittest.TestCase):
    """Tests for verifying how printing works."""
    def setUp(self):
        self.jpxfile = glymur.data.jpxfile()
        self.jp2file = glymur.data.nemo()
        self.j2kfile = glymur.data.goodstuff()

        # Reset printoptions for every test.
        glymur.set_printoptions(short=False, xml=True, codestream=True)

    def tearDown(self):
        pass

    def test_version_info(self):
        """Should be able to print(glymur.version.info)"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(glymur.version.info)
            actual = fake_out.getvalue().strip()

        self.assertTrue(True)

    @unittest.skipIf(sys.hexversion < 0x03000000, "Needs unittest in 3.x.")
    def test_unknown_superbox(self):
        """Verify that we can handle an unknown superbox."""
        with tempfile.NamedTemporaryFile(suffix='.jpx') as tfile:
            with open(self.jpxfile, 'rb') as ifile:
                tfile.write(ifile.read())
            
            # Add the header for an unknwon superbox.
            write_buffer = struct.pack('>I4s', 20, 'grp '.encode())
            tfile.write(write_buffer)
            write_buffer = struct.pack('>I4sI', 12, 'free'.encode(), 0)
            tfile.write(write_buffer)
            tfile.flush()

            with self.assertWarns(UserWarning):
                jpx = Jp2k(tfile.name)
            glymur.set_printoptions(short=True)
            with patch('sys.stdout', new=StringIO()) as fake_out:
                print(jpx.box[-1])
                actual = fake_out.getvalue().strip()
            lines = ['Unknown Box (grp ) @ (695609, 20)',
                     '    Free Box (free) @ (695617, 12)']
            expected = '\n'.join(lines)
            self.assertEqual(actual, expected)

    def test_printoptions_bad_argument(self):
        """Verify error when bad parameter to set_printoptions"""
        with self.assertRaises(TypeError):
            glymur.set_printoptions(hi='low')

    def test_propts_no_codestream_then_no_xml(self):
        """Verify printed output when codestream=False and xml=False, #162"""
        # The print options should be persistent across invocations.
        glymur.set_printoptions(codestream=False)
        glymur.set_printoptions(xml=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        self.assertEqual(actual, fixtures.nemo_dump_no_codestream_no_xml)

    def test_printopt_no_codestr_or_xml(self):
        """Verify printed output when codestream=False and xml=False"""
        glymur.set_printoptions(codestream=False, xml=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        self.assertEqual(actual, fixtures.nemo_dump_no_codestream_no_xml)

    def test_printoptions_no_codestream(self):
        """Verify printed output when codestream=False"""
        glymur.set_printoptions(codestream=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        self.assertEqual(actual, fixtures.nemo_dump_no_codestream)

    def test_printoptions_no_xml(self):
        """Verify printed output when xml=False"""
        glymur.set_printoptions(xml=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        expected = fixtures.nemo_dump_no_xml
        self.assertEqual(actual, expected)

    def test_printoptions_short(self):
        """Verify printed output when short=True"""
        glymur.set_printoptions(short=True)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        self.assertEqual(actual, fixtures.nemo_dump_short)

    def test_asoc_label_box(self):
        """verify printing of asoc, label boxes"""
        # Construct a fake file with an asoc and a label box, as
        # OpenJPEG doesn't have such a file.
        data = glymur.Jp2k(self.jp2file).read(rlevel=1)
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile:
            j = glymur.Jp2k(tfile.name, 'wb')
            j.write(data)

            with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile2:

                # Offset of the codestream is where we start.
                wbuffer = tfile.read(77)
                tfile2.write(wbuffer)

                # read the rest of the file, it's the codestream.
                codestream = tfile.read()

                # Write the asoc superbox.
                # Length = 36, id is 'asoc'.
                wbuffer = struct.pack('>I4s', int(56), b'asoc')
                tfile2.write(wbuffer)

                # Write the contained label box
                wbuffer = struct.pack('>I4s', int(13), b'lbl ')
                tfile2.write(wbuffer)
                tfile2.write('label'.encode())

                # Write the xml box
                # Length = 36, id is 'xml '.
                wbuffer = struct.pack('>I4s', int(35), b'xml ')
                tfile2.write(wbuffer)

                wbuffer = '<test>this is a test</test>'
                wbuffer = wbuffer.encode()
                tfile2.write(wbuffer)

                # Now append the codestream.
                tfile2.write(codestream)
                tfile2.flush()

                jasoc = glymur.Jp2k(tfile2.name)
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    print(jasoc.box[3])
                    actual = fake_out.getvalue().strip()
                lines = ['Association Box (asoc) @ (77, 56)',
                         '    Label Box (lbl ) @ (85, 13)',
                         '        Label:  label',
                         '    XML Box (xml ) @ (98, 35)',
                         '        <test>this is a test</test>']
                expected = '\n'.join(lines)
                self.assertEqual(actual, expected)

    def test_jp2dump(self):
        """basic jp2dump test"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            glymur.jp2dump(self.jp2file)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)
        self.assertEqual(actual, fixtures.nemo_dump_full)

    def test_entire_file(self):
        """verify output from printing entire file"""
        j = glymur.Jp2k(self.jp2file)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j)
            actual = fake_out.getvalue().strip()

        # Get rid of the filename line, as it is not set in stone.
        lst = actual.split('\n')
        lst = lst[1:]
        actual = '\n'.join(lst)

        self.assertEqual(actual, fixtures.nemo_dump_full)

    def test_coc_segment(self):
        """verify printing of COC segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[6])
            actual = fake_out.getvalue().strip()

        lines = ['COC marker segment @ (3356, 9)',
                 '    Associated component:  1',
                 '    Coding style for this component:  '
                 + 'Entropy coder, PARTITION = 0',
                 '    Coding style parameters:',
                 '        Number of resolutions:  2',
                 '        Code block height, width:  (64 x 64)',
                 '        Wavelet transform:  5-3 reversible',
                 '        Code block context:',
                 '            Selective arithmetic coding bypass:  False',
                 '            Reset context probabilities '
                 + 'on coding pass boundaries:  False',
                 '            Termination on each coding pass:  False',
                 '            Vertically stripe causal context:  False',
                 '            Predictable termination:  False',
                 '            Segmentation symbols:  False']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_cod_segment(self):
        """verify printing of COD segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[2])
            actual = fake_out.getvalue().strip()

        lines = ['COD marker segment @ (3282, 12)',
                 '    Coding style:',
                 '        Entropy coder, without partitions',
                 '        SOP marker segments:  False',
                 '        EPH marker segments:  False',
                 '    Coding style parameters:',
                 '        Progression order:  LRCP',
                 '        Number of layers:  2',
                 '        Multiple component transformation usage:  '
                 + 'reversible',
                 '        Number of resolutions:  2',
                 '        Code block height, width:  (64 x 64)',
                 '        Wavelet transform:  5-3 reversible',
                 '        Precinct size:  default, 2^15 x 2^15',
                 '        Code block context:',
                 '            Selective arithmetic coding bypass:  False',
                 '            Reset context probabilities on coding '
                 + 'pass boundaries:  False',
                 '            Termination on each coding pass:  False',
                 '            Vertically stripe causal context:  False',
                 '            Predictable termination:  False',
                 '            Segmentation symbols:  False']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_eoc_segment(self):
        """verify printing of eoc segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[-1])
            actual = fake_out.getvalue().strip()

        lines = ['EOC marker segment @ (1135517, 0)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_qcc_segment(self):
        """verify printing of qcc segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[7])
            actual = fake_out.getvalue().strip()

        lines = ['QCC marker segment @ (3367, 8)',
                 '    Associated Component:  1',
                 '    Quantization style:  no quantization, 2 guard bits',
                 '    Step size:  [(0, 8), (0, 9), (0, 9), (0, 10)]']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_qcd_segment_5x3_transform(self):
        """verify printing of qcd segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[3])
            actual = fake_out.getvalue().strip()

        lines = ['QCD marker segment @ (3296, 7)',
                 '    Quantization style:  no quantization, 2 guard bits',
                 '    Step size:  [(0, 8), (0, 9), (0, 9), (0, 10)]']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_siz_segment(self):
        """verify printing of SIZ segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[1])
            actual = fake_out.getvalue().strip()

        lines = ['SIZ marker segment @ (3233, 47)',
                 '    Profile:  no profile',
                 '    Reference Grid Height, Width:  (1456 x 2592)',
                 '    Vertical, Horizontal Reference Grid Offset:  (0 x 0)',
                 '    Reference Tile Height, Width:  (1456 x 2592)',
                 '    Vertical, Horizontal Reference Tile Offset:  (0 x 0)',
                 '    Bitdepth:  (8, 8, 8)',
                 '    Signed:  (False, False, False)',
                 '    Vertical, Horizontal Subsampling:  '
                 + '((1, 1), (1, 1), (1, 1))']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_soc_segment(self):
        """verify printing of SOC segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[0])
            actual = fake_out.getvalue().strip()

        lines = ['SOC marker segment @ (3231, 0)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_sod_segment(self):
        """verify printing of SOD segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[10])
            actual = fake_out.getvalue().strip()

        lines = ['SOD marker segment @ (3398, 0)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_sot_segment(self):
        """verify printing of SOT segment"""
        j = glymur.Jp2k(self.jp2file)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[5])
            actual = fake_out.getvalue().strip()

        lines = ['SOT marker segment @ (3344, 10)',
                 '    Tile part index:  0',
                 '    Tile part length:  1132173',
                 '    Tile part instance:  0',
                 '    Number of tile parts:  1']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_xmp(self):
        """Verify the printing of a UUID/XMP box."""
        j = glymur.Jp2k(self.jp2file)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[3])
            actual = fake_out.getvalue().strip()

        expected = fixtures.nemo_xmp_box
        self.assertEqual(actual, expected)

    def test_codestream(self):
        """verify printing of entire codestream"""
        j = glymur.Jp2k(self.jp2file)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.get_codestream())
            actual = fake_out.getvalue().strip()
        lst = ['Codestream:',
               '    SOC marker segment @ (3231, 0)',
               '    SIZ marker segment @ (3233, 47)',
               '        Profile:  no profile',
               '        Reference Grid Height, Width:  (1456 x 2592)',
               '        Vertical, Horizontal Reference Grid Offset:  (0 x 0)',
               '        Reference Tile Height, Width:  (1456 x 2592)',
               '        Vertical, Horizontal Reference Tile Offset:  (0 x 0)',
               '        Bitdepth:  (8, 8, 8)',
               '        Signed:  (False, False, False)',
               '        Vertical, Horizontal Subsampling:  '
               + '((1, 1), (1, 1), (1, 1))',
               '    COD marker segment @ (3282, 12)',
               '        Coding style:',
               '            Entropy coder, without partitions',
               '            SOP marker segments:  False',
               '            EPH marker segments:  False',
               '        Coding style parameters:',
               '            Progression order:  LRCP',
               '            Number of layers:  2',
               '            Multiple component transformation usage:  '
               + 'reversible',
               '            Number of resolutions:  2',
               '            Code block height, width:  (64 x 64)',
               '            Wavelet transform:  5-3 reversible',
               '            Precinct size:  default, 2^15 x 2^15',
               '            Code block context:',
               '                Selective arithmetic coding bypass:  False',
               '                Reset context probabilities on '
               + 'coding pass boundaries:  False',
               '                Termination on each coding pass:  False',
               '                Vertically stripe causal context:  False',
               '                Predictable termination:  False',
               '                Segmentation symbols:  False',
               '    QCD marker segment @ (3296, 7)',
               '        Quantization style:  no quantization, '
               + '2 guard bits',
               '        Step size:  [(0, 8), (0, 9), (0, 9), (0, 10)]',
               '    CME marker segment @ (3305, 37)',
               '        "Created by OpenJPEG version 2.0.0"']
        expected = '\n'.join(lst)
        self.assertEqual(actual, expected)

    @unittest.skipIf(sys.hexversion < 0x03000000,
                     "Only trusting python3 for printing non-ascii chars")
    def test_xml_latin1(self):
        """Should be able to print an XMLBox with utf-8 encoding (latin1)."""
        # Seems to be inconsistencies between different versions of python2.x
        # as to what gets printed.
        #
        # 2.7.5 (fedora 19) prints xml entities.
        # 2.7.3 seems to want to print hex escapes.
        text = u"""<flow>Strömung</flow>"""
        if sys.hexversion < 0x03000000:
            xml = ET.parse(StringIO(text.encode('utf-8')))
        else:
            xml = ET.parse(StringIO(text))

        xmlbox = glymur.jp2box.XMLBox(xml=xml)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(xmlbox)
            actual = fake_out.getvalue().strip()
            if sys.hexversion < 0x03000000:
                lines = ["XML Box (xml ) @ (-1, 0)",
                         "    <flow>Str\xc3\xb6mung</flow>"]
            else:
                lines = ["XML Box (xml ) @ (-1, 0)",
                         "    <flow>Strömung</flow>"]
            expected = '\n'.join(lines)
            self.assertEqual(actual, expected)

    @unittest.skipIf(sys.hexversion < 0x03000000,
                     "Only trusting python3 for printing non-ascii chars")
    def test_xml_cyrrilic(self):
        """Should be able to print an XMLBox with utf-8 encoding (cyrrillic)."""
        # Seems to be inconsistencies between different versions of python2.x
        # as to what gets printed.
        #
        # 2.7.5 (fedora 19) prints xml entities.
        # 2.7.3 seems to want to print hex escapes.
        text = u"""<country>Россия</country>"""
        if sys.hexversion < 0x03000000:
            xml = ET.parse(StringIO(text.encode('utf-8')))
        else:
            xml = ET.parse(StringIO(text))

        xmlbox = glymur.jp2box.XMLBox(xml=xml)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(xmlbox)
            actual = fake_out.getvalue().strip()
            if sys.hexversion < 0x03000000:
                lines = ["XML Box (xml ) @ (-1, 0)",
                         "    <country>&#1056;&#1086;&#1089;&#1089;&#1080;&#1103;</country>"]
            else:
                lines = ["XML Box (xml ) @ (-1, 0)",
                         "    <country>Россия</country>"]

            expected = '\n'.join(lines)
            self.assertEqual(actual, expected)

    @unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
    def test_less_common_boxes(self):
        """verify uinf, ulst, url, res, resd, resc box printing"""
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile:
            with open(self.jp2file, 'rb') as ifile:
                # Everything up until the jp2c box.
                wbuffer = ifile.read(77)
                tfile.write(wbuffer)

                # Write the UINF superbox
                # Length = 50, id is uinf.
                wbuffer = struct.pack('>I4s', int(50), b'uinf')
                tfile.write(wbuffer)

                # Write the ULST box.
                # Length is 26, 1 UUID, hard code that UUID as zeros.
                wbuffer = struct.pack('>I4sHIIII', int(26), b'ulst', int(1),
                                      int(0), int(0), int(0), int(0))
                tfile.write(wbuffer)

                # Write the URL box.
                # Length is 16, version is one byte, flag is 3 bytes, url
                # is the rest.
                wbuffer = struct.pack('>I4sBBBB',
                                      int(16), b'url ',
                                      int(0), int(0), int(0), int(0))
                tfile.write(wbuffer)

                wbuffer = struct.pack('>ssss', b'a', b'b', b'c', b'd')
                tfile.write(wbuffer)

                # Start the resolution superbox.
                wbuffer = struct.pack('>I4s', int(44), b'res ')
                tfile.write(wbuffer)

                # Write the capture resolution box.
                wbuffer = struct.pack('>I4sHHHHBB',
                                      int(18), b'resc',
                                      int(1), int(1), int(1), int(1),
                                      int(0), int(1))
                tfile.write(wbuffer)

                # Write the display resolution box.
                wbuffer = struct.pack('>I4sHHHHBB',
                                      int(18), b'resd',
                                      int(1), int(1), int(1), int(1),
                                      int(1), int(0))
                tfile.write(wbuffer)

                # Get the rest of the input file.
                wbuffer = ifile.read()
                tfile.write(wbuffer)
                tfile.flush()

            jp2k = glymur.Jp2k(tfile.name)
            with patch('sys.stdout', new=StringIO()) as fake_out:
                print(jp2k.box[3])
                print(jp2k.box[4])
                actual = fake_out.getvalue().strip()
            lines = ['UUIDInfo Box (uinf) @ (77, 50)',
                     '    UUID List Box (ulst) @ (85, 26)',
                     '        UUID[0]:  00000000-0000-0000-0000-000000000000',
                     '    Data Entry URL Box (url ) @ (111, 16)',
                     '        Version:  0',
                     '        Flag:  0 0 0',
                     '        URL:  "abcd"',
                     'Resolution Box (res ) @ (127, 44)',
                     '    Capture Resolution Box (resc) @ (135, 18)',
                     '        VCR:  1.0',
                     '        HCR:  10.0',
                     '    Display Resolution Box (resd) @ (153, 18)',
                     '        VDR:  10.0',
                     '        HDR:  1.0']

            expected = '\n'.join(lines)
            self.assertEqual(actual, expected)

    @unittest.skipIf(sys.hexversion < 0x03000000,
                     "Ordered dicts not printing well in 2.7")
    def test_exif_uuid(self):
        """Verify printing of exif information"""
        with tempfile.NamedTemporaryFile(suffix='.jp2', mode='wb') as tfile:

            with open(self.jp2file, 'rb') as ifptr:
                tfile.write(ifptr.read())

            # Write L, T, UUID identifier.
            tfile.write(struct.pack('>I4s', 76, b'uuid'))
            tfile.write(b'JpgTiffExif->JP2')

            tfile.write(b'Exif\x00\x00')
            xbuffer = struct.pack('<BBHI', 73, 73, 42, 8)
            tfile.write(xbuffer)

            # We will write just three tags.
            tfile.write(struct.pack('<H', 3))

            # The "Make" tag is tag no. 271.
            tfile.write(struct.pack('<HHII', 256, 4, 1, 256))
            tfile.write(struct.pack('<HHII', 257, 4, 1, 512))
            tfile.write(struct.pack('<HHI4s', 271, 2, 3, b'HTC\x00'))
            tfile.flush()

            j = glymur.Jp2k(tfile.name)

            with patch('sys.stdout', new=StringIO()) as fake_out:
                print(j.box[5])
                actual = fake_out.getvalue().strip()

        lines = ["UUID Box (uuid) @ (1135519, 76)",
                 "    UUID:  4a706754-6966-6645-7869-662d3e4a5032 (EXIF)",
                 "    UUID Data:  OrderedDict([('ImageWidth', 256), ('ImageLength', 512), ('Make', 'HTC')])"]

        expected = '\n'.join(lines)

        self.assertEqual(actual, expected)


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
class TestPrintingOpjDataRoot(unittest.TestCase):
    """Tests for verifying printing. restricted to OPJ_DATA_ROOT files."""
    def setUp(self):
        self.jpxfile = glymur.data.jpxfile()
        self.jp2file = glymur.data.nemo()
        self.j2kfile = glymur.data.goodstuff()

        # Reset printoptions for every test.
        glymur.set_printoptions(short=False, xml=True, codestream=True)

    def tearDown(self):
        pass

    def test_cinema_profile(self):
        """Should print Cinema 2K when the profile is 3."""
        filename = opj_data_file('input/nonregression/_00042.j2k')
        j2k = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            c = j2k.get_codestream()
            print(c.segment[1])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.cinema2k_profile)

    def test_invalid_colorspace(self):
        """An invalid colorspace shouldn't cause an error."""
        filename = opj_data_file('input/nonregression/edf_c2_1103421.jp2')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(jp2)

    def test_bad_rsiz(self):
        """Should still be able to print if rsiz is bad, issue196"""
        filename = opj_data_file('input/nonregression/edf_c2_1002767.jp2')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            j = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j)

    def test_bad_wavelet_transform(self):
        """Should still be able to print if wavelet xform is bad, issue195"""
        filename = opj_data_file('input/nonregression/edf_c2_10025.jp2')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            j = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j)

    def test_invalid_progression_order(self):
        """Should still be able to print even if prog order is invalid."""
        jfile = opj_data_file('input/nonregression/2977.pdf.asan.67.2198.jp2')
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            jp2 = Jp2k(jfile)
        codestream = jp2.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[2])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.issue_186_progression_order)

    def test_crg(self):
        """verify printing of CRG segment"""
        filename = opj_data_file('input/conformance/p0_03.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[-5])
            actual = fake_out.getvalue().strip()
        lines = ['CRG marker segment @ (87, 6)',
                 '    Vertical, Horizontal offset:  (0.50, 1.00)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_rgn(self):
        """verify printing of RGN segment"""
        filename = opj_data_file('input/conformance/p0_03.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[12])
            actual = fake_out.getvalue().strip()
        lines = ['RGN marker segment @ (310, 5)',
                 '    Associated component:  0',
                 '    ROI style:  0',
                 '    Parameter:  7']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_sop(self):
        """verify printing of SOP segment"""
        filename = opj_data_file('input/conformance/p0_03.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[-2])
            actual = fake_out.getvalue().strip()
        lines = ['SOP marker segment @ (12836, 4)',
                 '    Nsop:  15']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_cme(self):
        """Test printing a CME or comment marker segment."""
        filename = opj_data_file('input/conformance/p0_02.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        # 2nd to last segment in the main header
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[-2])
            actual = fake_out.getvalue().strip()
        lines = ['CME marker segment @ (85, 45)',
                 '    "Creator: AV-J2K (c) 2000,2001 Algo Vision"']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_plt_segment(self):
        """verify printing of PLT segment"""
        filename = opj_data_file('input/conformance/p0_07.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[49935])
            actual = fake_out.getvalue().strip()

        lines = ['PLT marker segment @ (7871146, 38)',
                 '    Index:  0',
                 '    Iplt:  [9, 122, 19, 30, 27, 9, 41, 62, 18, 29, 261,'
                 + ' 55, 82, 299, 93, 941, 951, 687, 1729, 1443, 1008, 2168,'
                 + ' 2188, 2223]']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_pod_segment(self):
        """verify printing of POD segment"""
        filename = opj_data_file('input/conformance/p0_13.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[8])
            actual = fake_out.getvalue().strip()

        lines = ['POD marker segment @ (878, 20)',
                 '    Progression change 0:',
                 '        Resolution index start:  0',
                 '        Component index start:  0',
                 '        Layer index end:  1',
                 '        Resolution index end:  33',
                 '        Component index end:  128',
                 '        Progression order:  RLCP',
                 '    Progression change 1:',
                 '        Resolution index start:  0',
                 '        Component index start:  128',
                 '        Layer index end:  1',
                 '        Resolution index end:  33',
                 '        Component index end:  257',
                 '        Progression order:  CPRL']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_ppm_segment(self):
        """verify printing of PPM segment"""
        filename = opj_data_file('input/conformance/p1_03.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[9])
            actual = fake_out.getvalue().strip()

        lines = ['PPM marker segment @ (213, 43712)',
                 '    Index:  0',
                 '    Data:  43709 uninterpreted bytes']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_ppt_segment(self):
        """verify printing of ppt segment"""
        filename = opj_data_file('input/conformance/p1_06.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream(header_only=False)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[6])
            actual = fake_out.getvalue().strip()

        lines = ['PPT marker segment @ (155, 109)',
                 '    Index:  0',
                 '    Packet headers:  106 uninterpreted bytes']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_tlm_segment(self):
        """verify printing of TLM segment"""
        filename = opj_data_file('input/conformance/p0_15.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[10])
            actual = fake_out.getvalue().strip()

        lines = ['TLM marker segment @ (268, 28)',
                 '    Index:  0',
                 '    Tile number:  (0, 1, 2, 3)',
                 '    Length:  (4267, 2117, 4080, 2081)']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_xml(self):
        """verify printing of XML box"""
        filename = opj_data_file('input/conformance/file1.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.file1_xml)

    def test_channel_definition(self):
        """verify printing of cdef box"""
        filename = opj_data_file('input/conformance/file2.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2].box[2])
            actual = fake_out.getvalue().strip()
        lines = ['Channel Definition Box (cdef) @ (81, 28)',
                 '    Channel 0 (color) ==> (3)',
                 '    Channel 1 (color) ==> (2)',
                 '    Channel 2 (color) ==> (1)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_component_mapping(self):
        """verify printing of cmap box"""
        filename = opj_data_file('input/conformance/file9.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2].box[2])
            actual = fake_out.getvalue().strip()
        lines = ['Component Mapping Box (cmap) @ (848, 20)',
                 '    Component 0 ==> palette column 0',
                 '    Component 0 ==> palette column 1',
                 '    Component 0 ==> palette column 2']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_palette7(self):
        """verify printing of pclr box"""
        filename = opj_data_file('input/conformance/file9.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2].box[1])
            actual = fake_out.getvalue().strip()
        lines = ['Palette Box (pclr) @ (66, 782)',
                 '    Size:  (256 x 3)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    @unittest.skip("file7 no longer has a rreq")
    def test_rreq(self):
        """verify printing of reader requirements box"""
        filename = opj_data_file('input/nonregression/text_GBR.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.text_GBR_rreq)

    def test_differing_subsamples(self):
        """verify printing of SIZ with different subsampling... Issue 86."""
        filename = opj_data_file('input/conformance/p0_05.j2k')
        j = glymur.Jp2k(filename)
        codestream = j.get_codestream()
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(codestream.segment[1])
            actual = fake_out.getvalue().strip()
        lines = ['SIZ marker segment @ (2, 50)',
                 '    Profile:  0',
                 '    Reference Grid Height, Width:  (1024 x 1024)',
                 '    Vertical, Horizontal Reference Grid Offset:  (0 x 0)',
                 '    Reference Tile Height, Width:  (1024 x 1024)',
                 '    Vertical, Horizontal Reference Tile Offset:  (0 x 0)',
                 '    Bitdepth:  (8, 8, 8, 8)',
                 '    Signed:  (False, False, False, False)',
                 '    Vertical, Horizontal Subsampling:  '
                 + '((1, 1), (1, 1), (2, 2), (2, 2))']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_palette_box(self):
        """Verify that palette (pclr) boxes are printed without error."""
        filename = opj_data_file('input/conformance/file9.jp2')
        j = glymur.Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(j.box[2].box[1])
            actual = fake_out.getvalue().strip()
        lines = ['Palette Box (pclr) @ (66, 782)',
                 '    Size:  (256 x 3)']
        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_icc_profile(self):
        """verify icc profile printing with a jpx"""
        # ICC profiles may be used in JP2, but the approximation field should
        # be zero unless we have jpx.  This file does both.
        filename = opj_data_file('input/nonregression/text_GBR.jp2')
        with warnings.catch_warnings():
            # brand is 'jp2 ', but has any icc profile.
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(jp2.box[3].box[1])
            actual = fake_out.getvalue().strip()
        if sys.hexversion < 0x03000000:
            expected = text_gbr_27
        elif sys.hexversion < 0x03040000:
            expected = text_gbr_33
        else:
            expected = text_gbr_34

        self.assertEqual(actual, expected)

    def test_uuid(self):
        """verify printing of UUID box"""
        filename = opj_data_file('input/nonregression/text_GBR.jp2')
        with warnings.catch_warnings():
            # brand is 'jp2 ', but has any icc profile.
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)

        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(jp2.box[4])
            actual = fake_out.getvalue().strip()
        lines = ['UUID Box (uuid) @ (1544, 25)',
                 '    UUID:  3a0d0218-0ae9-4115-b376-4bca41ce0e71 (unknown)',
                 '    UUID Data:  1 bytes']

        expected = '\n'.join(lines)
        self.assertEqual(actual, expected)

    def test_issue182(self):
        """Should not show the format string in output."""
        # The cmap box is wildly broken, but printing was still wrong.
        # Format strings like %d were showing up in the output.
        filename = opj_data_file('input/nonregression/mem-b2ace68c-1381.jp2')

        with warnings.catch_warnings():
            # Ignore warning about bad pclr box.
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(jp2.box[3].box[3])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.issue_182_cmap)

    def test_issue183(self):
        filename = opj_data_file('input/nonregression/orb-blue10-lin-jp2.jp2')

        with warnings.catch_warnings():
            # Ignore warning about bad pclr box.
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)
        with patch('sys.stdout', new=StringIO()) as fake_out:
            print(jp2.box[2].box[1])
            actual = fake_out.getvalue().strip()
        self.assertEqual(actual, fixtures.issue_183_colr)

    def test_bom(self):
        """Byte order markers are illegal in UTF-8.  Issue 185"""
        filename = opj_data_file(os.path.join('input',
                                              'nonregression',
                                              'issue171.jp2'))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            jp2 = Jp2k(filename)
            with patch('sys.stdout', new=StringIO()) as fake_out:
                # No need to verify, it's enough that we don't error out.
                print(jp2)

        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
