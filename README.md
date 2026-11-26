
# Automated Microscope Cell Counter 🔬

A biomedical image analysis application that uses computer vision to automatically detect, count, and analyze cells in microscopy images.

Built with **Django, Django REST Framework, OpenCV, and scikit-image**, this project explores image processing and cell segmentation techniques for biomedical research applications.

## Features

- Upload and process microscopy images
- Detect and count cells using computer vision
- Apply image preprocessing and segmentation techniques
- Measure cell properties such as area and position
- Generate annotated images highlighting detected cells
- Access analysis results through a REST API

## Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Image Processing:** OpenCV, scikit-image, NumPy
- **Image Handling:** Pillow
- **AI Assistance:** GitHub Copilot

## Getting Started

```bash
git clone https://github.com/Nepul321/Automated-Microscope-Cell-Counter.git
cd Automated-Microscope-Cell-Counter

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Media uploads

Uploaded files are stored under the project-level `media/` directory and served
at `/media/` while `DEBUG=True`. The directory is excluded from version control.
For an upload model, use a Django `FileField` or `ImageField` with an `upload_to`
path; HTML upload forms must use `enctype="multipart/form-data"` and views must
read files from `request.FILES`.

The development server's media serving is not suitable for production. Configure
production storage and web-server or object-storage delivery before accepting
uploads in a deployed environment.

## Authentication

The website's custom session-authentication pages are under `/accounts/`:

- `/accounts/sign-up/`, `/accounts/login/`, and `/accounts/logout/`
- `/accounts/account/` and `/accounts/change-password/` (authenticated)
- `/accounts/forgot-password/` and the password-reset confirmation link

The API is under `/api/auth/`. Same-origin API requests may authenticate with a
website session or a DRF token. Cross-origin API requests cannot authenticate with
a session and must use `Authorization: Token <key>`. Obtain a token with
`POST /api/auth/token/`; authenticated API endpoints include `/account/` and
`/change-password/`. Request a password-reset email with public
`POST /api/auth/forgot-password/`; it sends the same short website reset link as
the website form. To permit a browser frontend on another origin, set
`CORS_ALLOWED_ORIGINS` to a comma-separated list of trusted origins; cross-origin
requests do not receive credentialed session access.

Password reset messages use Django's console email backend in this development
setup, so the reset URL is printed in the server console rather than delivered.
Reset tokens are stored hashed, expire according to Django's
`PASSWORD_RESET_TIMEOUT`, and can be used only once. Apply migrations after
updating the application before requesting a new reset link.

## Roadmap

- [ ] Implement image upload API
- [ ] Develop cell detection and counting algorithms
- [ ] Generate annotated microscopy images
- [ ] Return cell measurements through REST endpoints
- [ ] Evaluate detection accuracy using public datasets
- [ ] Build an interactive frontend

## Disclaimer

This project is intended for educational and research purposes only and is not designed for clinical diagnosis or medical decision-making.
