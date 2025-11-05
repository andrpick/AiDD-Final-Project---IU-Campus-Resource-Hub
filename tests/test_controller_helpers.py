"""
Unit tests for controller helper utilities.
Tests common controller patterns like permission checking, image handling, and service result processing.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from werkzeug.datastructures import FileStorage
from flask import Flask
from flask_login import LoginManager
import os
import tempfile
import json

from src.utils.controller_helpers import (
    check_resource_permission,
    handle_service_result,
    allowed_image_file,
    save_uploaded_images,
    delete_image_file,
    parse_existing_images,
    combine_images,
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_COUNT
)


@pytest.fixture
def app_context():
    """Create Flask application context for testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['TESTING'] = True
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    with app.app_context():
        yield app


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = Mock()
    user.user_id = 1
    user.is_admin = Mock(return_value=False)
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user object."""
    user = Mock()
    user.user_id = 2
    user.is_admin = Mock(return_value=True)
    user.is_authenticated = True
    return user


@pytest.fixture
def temp_upload_folder():
    """Create a temporary upload folder for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCheckResourcePermission:
    """Tests for check_resource_permission function."""
    
    @patch('src.utils.controller_helpers.current_user')
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.url_for')
    @patch('src.utils.controller_helpers.redirect')
    def test_check_permission_not_authenticated(self, mock_redirect, mock_url_for, mock_flash, mock_current_user, app_context):
        """Test that unauthenticated users are redirected to login."""
        mock_current_user.is_authenticated = False
        mock_url_for.return_value = '/auth/login'
        mock_redirect.return_value = Mock()
        
        has_permission, response = check_resource_permission(1, 'Unauthorized.')
        
        assert has_permission == False
        assert response is not None
        mock_flash.assert_called_once_with('Please log in to access this page.', 'error')
        mock_url_for.assert_called_once_with('auth.login')
        mock_redirect.assert_called_once()
    
    @patch('src.utils.controller_helpers.current_user')
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.redirect')
    def test_check_permission_owner(self, mock_redirect, mock_flash, mock_current_user, app_context, mock_user):
        """Test that resource owner has permission."""
        mock_current_user.user_id = 1
        mock_current_user.is_admin = Mock(return_value=False)
        mock_current_user.is_authenticated = True
        
        has_permission, response = check_resource_permission(1, 'Unauthorized.')
        
        assert has_permission == True
        assert response is None
        mock_flash.assert_not_called()
    
    @patch('src.utils.controller_helpers.current_user')
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.redirect')
    def test_check_permission_admin(self, mock_redirect, mock_flash, mock_current_user, app_context, mock_admin_user):
        """Test that admin users have permission."""
        mock_current_user.user_id = 2
        mock_current_user.is_admin = Mock(return_value=True)
        mock_current_user.is_authenticated = True
        
        has_permission, response = check_resource_permission(1, 'Unauthorized.')
        
        assert has_permission == True
        assert response is None
        mock_flash.assert_not_called()
    
    @patch('src.utils.controller_helpers.current_user')
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.url_for')
    @patch('src.utils.controller_helpers.redirect')
    def test_check_permission_unauthorized_user(self, mock_redirect, mock_url_for, mock_flash, mock_current_user, app_context):
        """Test that non-owner, non-admin users are denied."""
        mock_current_user.user_id = 3
        mock_current_user.is_admin = Mock(return_value=False)
        mock_current_user.is_authenticated = True
        mock_url_for.return_value = '/'
        mock_redirect.return_value = Mock()
        
        has_permission, response = check_resource_permission(1, 'Custom error message.')
        
        assert has_permission == False
        assert response is not None
        mock_flash.assert_called_once_with('Custom error message.', 'error')
        mock_url_for.assert_called_once_with('home')
        mock_redirect.assert_called_once()


class TestHandleServiceResult:
    """Tests for handle_service_result function."""
    
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.redirect')
    def test_handle_service_result_success(self, mock_redirect, mock_flash, app_context):
        """Test successful service result handling."""
        mock_redirect_func = Mock(return_value=Mock())
        result = {
            'success': True,
            'data': {'resource_id': 1}
        }
        
        response = handle_service_result(result, 'Success!', mock_redirect_func)
        
        mock_flash.assert_called_once_with('Success!', 'success')
        mock_redirect_func.assert_called_once_with(resource_id=1)
    
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.redirect')
    def test_handle_service_result_error_with_redirect(self, mock_redirect, mock_flash, app_context):
        """Test error service result with custom error redirect."""
        mock_error_redirect = Mock(return_value=Mock())
        result = {
            'success': False,
            'error': 'Resource not found.'
        }
        
        response = handle_service_result(result, 'Success!', Mock(), mock_error_redirect)
        
        mock_flash.assert_called_once_with('Resource not found.', 'error')
        mock_error_redirect.assert_called_once()
    
    @patch('src.utils.controller_helpers.flash')
    @patch('src.utils.controller_helpers.url_for')
    @patch('src.utils.controller_helpers.redirect')
    def test_handle_service_result_error_no_redirect(self, mock_redirect, mock_url_for, mock_flash, app_context):
        """Test error service result without custom error redirect."""
        mock_url_for.return_value = '/'
        mock_redirect.return_value = Mock()
        result = {
            'success': False,
            'error': 'Resource not found.'
        }
        
        response = handle_service_result(result, 'Success!', Mock())
        
        mock_flash.assert_called_once_with('Resource not found.', 'error')
        mock_url_for.assert_called_once_with('home')
        mock_redirect.assert_called_once()


class TestAllowedImageFile:
    """Tests for allowed_image_file function."""
    
    def test_allowed_image_extensions(self):
        """Test that all allowed extensions are recognized."""
        for ext in ALLOWED_IMAGE_EXTENSIONS:
            assert allowed_image_file(f'test.{ext}') == True
            assert allowed_image_file(f'test.{ext.upper()}') == True
    
    def test_disallowed_extensions(self):
        """Test that disallowed extensions are rejected."""
        assert allowed_image_file('test.txt') == False
        assert allowed_image_file('test.exe') == False
        assert allowed_image_file('test.pdf') == False
        assert allowed_image_file('test.doc') == False
    
    def test_no_extension(self):
        """Test that files without extensions are rejected."""
        assert allowed_image_file('test') == False
        assert allowed_image_file('test.') == False
    
    def test_multiple_extensions(self):
        """Test that files with multiple extensions use the last one."""
        assert allowed_image_file('test.txt.jpg') == True
        assert allowed_image_file('test.jpg.txt') == False


class TestSaveUploadedImages:
    """Tests for save_uploaded_images function."""
    
    def test_save_uploaded_images_empty_list(self, temp_upload_folder):
        """Test that empty file list returns empty list."""
        result = save_uploaded_images([], temp_upload_folder)
        assert result == []
    
    def test_save_uploaded_images_valid_files(self, temp_upload_folder):
        """Test saving valid image files."""
        # Create mock file objects
        files = []
        for i, ext in enumerate(['jpg', 'png', 'webp']):
            file = Mock(spec=FileStorage)
            file.filename = f'test{i}.{ext}'
            file.save = Mock()
            files.append(file)
        
        result = save_uploaded_images(files, temp_upload_folder)
        
        assert len(result) == 3
        assert all('resources/' in path for path in result)
        assert all(path.endswith(ext) for path, ext in zip(result, ['jpg', 'png', 'webp']))
        assert all(file.save.called for file in files)
    
    def test_save_uploaded_images_invalid_files(self, temp_upload_folder):
        """Test that invalid files are skipped."""
        valid_file = Mock(spec=FileStorage)
        valid_file.filename = 'valid.jpg'
        valid_file.save = Mock()
        
        invalid_file = Mock(spec=FileStorage)
        invalid_file.filename = 'invalid.txt'
        
        files = [valid_file, invalid_file]
        
        result = save_uploaded_images(files, temp_upload_folder)
        
        assert len(result) == 1
        assert 'resources/' in result[0]
        valid_file.save.assert_called_once()
    
    def test_save_uploaded_images_empty_filename(self, temp_upload_folder):
        """Test that files with empty filenames are skipped."""
        file = Mock(spec=FileStorage)
        file.filename = ''
        
        result = save_uploaded_images([file], temp_upload_folder)
        
        assert result == []
    
    def test_save_uploaded_images_max_count(self, temp_upload_folder):
        """Test that only MAX_IMAGE_COUNT images are saved."""
        files = []
        for i in range(MAX_IMAGE_COUNT + 5):
            file = Mock(spec=FileStorage)
            file.filename = f'test{i}.jpg'
            file.save = Mock()
            files.append(file)
        
        result = save_uploaded_images(files, temp_upload_folder)
        
        assert len(result) == MAX_IMAGE_COUNT
        assert all(file.save.called for file in files[:MAX_IMAGE_COUNT])
    
    def test_save_uploaded_images_custom_subfolder(self, temp_upload_folder):
        """Test saving to custom subfolder."""
        file = Mock(spec=FileStorage)
        file.filename = 'test.jpg'
        file.save = Mock()
        
        result = save_uploaded_images([file], temp_upload_folder, subfolder='custom')
        
        assert len(result) == 1
        assert result[0].startswith('custom/')
        assert os.path.exists(os.path.join(temp_upload_folder, 'custom'))
    
    def test_save_uploaded_images_error_handling(self, temp_upload_folder):
        """Test that errors saving one file don't stop others."""
        file1 = Mock(spec=FileStorage)
        file1.filename = 'test1.jpg'
        file1.save = Mock(side_effect=Exception("Save error"))
        
        file2 = Mock(spec=FileStorage)
        file2.filename = 'test2.jpg'
        file2.save = Mock()
        
        result = save_uploaded_images([file1, file2], temp_upload_folder)
        
        # Should still save the second file despite error on first
        assert len(result) == 1
        assert file2.save.called


class TestDeleteImageFile:
    """Tests for delete_image_file function."""
    
    def test_delete_image_file_exists(self, temp_upload_folder):
        """Test deleting an existing image file."""
        # Create test file
        test_path = os.path.join(temp_upload_folder, 'resources', 'test.jpg')
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        with open(test_path, 'w') as f:
            f.write('test content')
        
        result = delete_image_file('resources/test.jpg', temp_upload_folder)
        
        assert result == True
        assert not os.path.exists(test_path)
    
    def test_delete_image_file_not_exists(self, temp_upload_folder):
        """Test deleting a non-existent file."""
        result = delete_image_file('resources/nonexistent.jpg', temp_upload_folder)
        
        assert result == False
    
    def test_delete_image_file_error(self, temp_upload_folder):
        """Test error handling when deleting file."""
        # Mock os.remove to raise exception
        with patch('src.utils.controller_helpers.os.remove', side_effect=PermissionError("Permission denied")):
            result = delete_image_file('resources/test.jpg', temp_upload_folder)
            assert result == False


class TestParseExistingImages:
    """Tests for parse_existing_images function."""
    
    def test_parse_existing_images_none(self):
        """Test parsing None."""
        result = parse_existing_images(None)
        assert result == []
    
    def test_parse_existing_images_empty_string(self):
        """Test parsing empty string."""
        result = parse_existing_images('')
        assert result == []
    
    def test_parse_existing_images_list(self):
        """Test parsing a list."""
        images = ['resources/img1.jpg', 'resources/img2.jpg']
        result = parse_existing_images(images)
        assert result == images
    
    def test_parse_existing_images_json_string(self):
        """Test parsing JSON string."""
        images = ['resources/img1.jpg', 'resources/img2.jpg']
        json_str = json.dumps(images)
        result = parse_existing_images(json_str)
        assert result == images
    
    def test_parse_existing_images_invalid_json(self):
        """Test parsing invalid JSON."""
        result = parse_existing_images('invalid json')
        assert result == []
    
    def test_parse_existing_images_non_list_json(self):
        """Test parsing JSON that's not a list."""
        result = parse_existing_images('{"key": "value"}')
        assert result == []


class TestCombineImages:
    """Tests for combine_images function."""
    
    def test_combine_images_no_removal(self):
        """Test combining images without removal."""
        existing = ['img1.jpg', 'img2.jpg']
        new = ['img3.jpg', 'img4.jpg']
        
        result = combine_images(existing, new)
        
        assert result == ['img1.jpg', 'img2.jpg', 'img3.jpg', 'img4.jpg']
    
    def test_combine_images_with_removal(self):
        """Test combining images with removal."""
        existing = ['img1.jpg', 'img2.jpg', 'img3.jpg']
        new = ['img4.jpg']
        removed = ['img2.jpg']
        
        result = combine_images(existing, new, removed)
        
        assert result == ['img1.jpg', 'img3.jpg', 'img4.jpg']
        assert 'img2.jpg' not in result
    
    def test_combine_images_empty_existing(self):
        """Test combining with empty existing list."""
        new = ['img1.jpg', 'img2.jpg']
        
        result = combine_images([], new)
        
        assert result == new
    
    def test_combine_images_empty_new(self):
        """Test combining with empty new list."""
        existing = ['img1.jpg', 'img2.jpg']
        
        result = combine_images(existing, [])
        
        assert result == existing
    
    def test_combine_images_remove_multiple(self):
        """Test removing multiple images."""
        existing = ['img1.jpg', 'img2.jpg', 'img3.jpg', 'img4.jpg']
        new = ['img5.jpg']
        removed = ['img2.jpg', 'img4.jpg']
        
        result = combine_images(existing, new, removed)
        
        assert result == ['img1.jpg', 'img3.jpg', 'img5.jpg']
        assert 'img2.jpg' not in result
        assert 'img4.jpg' not in result
    
    def test_combine_images_remove_nonexistent(self):
        """Test removing images that don't exist."""
        existing = ['img1.jpg', 'img2.jpg']
        new = ['img3.jpg']
        removed = ['img99.jpg']  # Doesn't exist
        
        result = combine_images(existing, new, removed)
        
        # Should still work, just ignore non-existent removals
        assert result == ['img1.jpg', 'img2.jpg', 'img3.jpg']
