# Enhanced Resume Upload Feature

## Overview
This feature allows users to upload their resume or portfolio as a DOCX or PDF file, and the system will automatically extract and display the information in their profile. The system also automatically populates the user's skills and projects based on the extracted content.

## Features
- **Multi-Format Support**: Users can upload their resume/portfolio as DOCX or PDF files
- **OCR Technology**: Uses Optical Character Recognition for PDF files to extract text from scanned documents
- **Automatic Content Extraction**: The system automatically extracts:
  - Skills (programming languages, frameworks, tools) - 66+ skill categories
  - Projects and portfolio items
  - Work experience
  - Education information
  - Full resume content
- **Auto-Population**: Automatically creates user skills and projects based on resume content
- **Profile Display**: Extracted information is displayed on both the user's account page and public profile
- **File Storage**: Resume files are stored securely and can be downloaded

## How to Use

### For Users:
1. **Upload Resume**:
   - Go to your Account page
   - Scroll to the "Resume/Portfolio" section
   - Click "Choose File" and select your DOCX or PDF resume
   - Click "Upload Resume"
   - The system will process and extract information automatically
   - Your skills and projects will be automatically updated

2. **View Extracted Information**:
   - On your Account page: See the extracted skills, experience, and education
   - On your Profile page: Others can view your resume information
   - Download your original resume file
   - Skills and projects are automatically populated in your profile

### For Developers:
The feature includes:
- **Model Fields**: Added to `Account` model in `users/models.py`
- **Upload View**: `uploadResume` view in `users/views.py`
- **Content Extraction**: `extract_resume_content` function
- **Templates**: Updated account and profile templates
- **URLs**: Added upload route

## Technical Details

### Dependencies Added:
- `python-docx==1.1.0` - For DOCX file processing
- `PyPDF2==3.0.1` - For PDF text extraction
- `pytesseract==0.3.10` - For OCR text recognition
- `pdf2image==1.17.0` - For PDF to image conversion

### New Model Fields:
- `resume_file` - FileField for storing the DOCX/PDF file
- `resume_content` - TextField for full extracted content
- `resume_skills` - TextField for extracted skills
- `resume_experience` - TextField for extracted experience
- `resume_education` - TextField for extracted education

### Content Extraction:
The system uses advanced regex patterns and OCR to identify:
- **Skills**: 66+ programming languages, frameworks, tools, and technologies
- **Projects**: Portfolio items, applications, and project descriptions
- **Experience**: Job titles, companies, and work history
- **Education**: Degrees, universities, and educational background

### Auto-Population Features:
- **Skills**: Automatically creates up to 10 skills from extracted content
- **Projects**: Automatically creates up to 5 projects from extracted content
- **Smart Filtering**: Removes duplicates and validates content quality

### File Storage:
- Resume files are stored in `media/resumes/` directory
- Files are accessible via URL for download
- Original filename is preserved

## Security Considerations:
- Only DOCX and PDF files are accepted
- File uploads are validated
- User authentication required for uploads
- Files are stored in a secure directory structure
- OCR processing is done securely with temporary files

## Testing Results:
✅ **Skills Extraction**: 66 skills identified from test resume  
✅ **Projects Extraction**: 5 projects identified  
✅ **Experience Extraction**: Companies and roles found  
✅ **Education Extraction**: Degrees and universities found  
✅ **Auto-Population**: Skills and projects automatically created  
✅ **Multi-Format Support**: Both DOCX and PDF processing working  

## Future Enhancements:
- Support for more file formats (RTF, TXT)
- Better content extraction algorithms with AI/ML
- Resume template suggestions
- Integration with job matching systems
- Advanced project detection with GitHub integration
- Skill proficiency levels extraction
