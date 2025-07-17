from flask import Flask, request, render_template_string
import os
from pathlib import Path
import socket
import qrcode
import threading
import time
import webbrowser
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB upload limit

# ✅ Upload folder on Desktop (OneDrive or normal)
desktop = Path.home() / "OneDrive/Desktop"
UPLOAD_FOLDER = desktop / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
print(f"[✓] Upload folder path: {UPLOAD_FOLDER}")

# ✅ Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.csv', '.xls', '.xlsx'}

# ✅ Check file extension
def is_allowed(filename):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

# ✅ HTML Page with form and style
HTML_PAGE = '''
<!doctype html>
<html>
  <head>
    <title>Upload Document</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      :root {
        --primary-color: #1976d2;
        --primary-hover: #125ea4;
        --success-color: #4caf50;
        --error-color: #f44336;
        --light-blue: #e3f2fd;
        --border-color: #90caf9;
      }
      
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        margin: 0;
        padding: 20px;
      }

      .upload-box {
        background-color: #ffffff;
        padding: 30px 20px;
        border-radius: 15px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
        text-align: center;
        width: 100%;
        max-width: 450px;
        animation: fadeIn 0.8s ease;
        transition: transform 0.3s ease;
      }

      @media (min-width: 768px) {
        .upload-box {
          padding: 40px 30px;
        }
      }

      .upload-box:hover {
        transform: translateY(-5px);
      }

      h1 {
        color: var(--primary-color);
        margin-bottom: 20px;
        font-weight: 600;
        font-size: 24px;
      }

      @media (min-width: 768px) {
        h1 {
          font-size: 28px;
          margin-bottom: 25px;
        }
      }

      .file-upload-wrapper {
        position: relative;
        margin-bottom: 15px;
      }

      @media (min-width: 768px) {
        .file-upload-wrapper {
          margin-bottom: 20px;
        }
      }

      .file-upload-label {
        display: block;
        padding: 30px 15px;
        border: 2px dashed var(--border-color);
        background-color: #f1f8ff;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
      }

      @media (min-width: 768px) {
        .file-upload-label {
          padding: 40px 20px;
        }
      }

      .file-upload-label:hover {
        background-color: var(--light-blue);
        border-color: var(--primary-color);
      }

      .file-upload-label i {
        font-size: 36px;
        color: var(--primary-color);
        margin-bottom: 8px;
        display: block;
      }

      @media (min-width: 768px) {
        .file-upload-label i {
          font-size: 48px;
          margin-bottom: 10px;
        }
      }

      .file-upload-label span {
        display: block;
        margin-top: 8px;
        color: #555;
        font-size: 14px;
      }

      @media (min-width: 768px) {
        .file-upload-label span {
          margin-top: 10px;
          font-size: inherit;
        }
      }

      .browse-text {
        color: var(--primary-color);
        font-weight: 600;
      }

      input[type="file"] {
        position: absolute;
        left: 0;
        top: 0;
        opacity: 0;
        width: 100%;
        height: 100%;
        cursor: pointer;
      }

      input[type="submit"] {
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 12px 25px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 10px rgba(25, 118, 210, 0.3);
      }

      @media (min-width: 768px) {
        input[type="submit"] {
          padding: 12px 30px;
          font-size: 15px;
        }
      }

      input[type="submit"]:hover {
        background-color: var(--primary-hover);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(25, 118, 210, 0.4);
      }

      input[type="submit"]:active {
        transform: translateY(0);
      }

      input[type="submit"]:disabled {
        background-color: #999;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
      }

      .file-info {
        margin-top: 12px;
        font-size: 13px;
        color: #555;
        display: none;
        word-break: break-word;
      }

      @media (min-width: 768px) {
        .file-info {
          margin-top: 15px;
          font-size: 14px;
        }
      }

      .status-message {
        margin-top: 15px;
        padding: 10px;
        border-radius: 8px;
        font-size: 14px;
        animation: fadeIn 0.5s ease;
        word-break: break-word;
      }

      @media (min-width: 768px) {
        .status-message {
          margin-top: 20px;
          padding: 12px;
          font-size: 16px;
        }
      }

      .success {
        background-color: rgba(76, 175, 80, 0.1);
        color: var(--success-color);
      }

      .error {
        background-color: rgba(244, 67, 54, 0.1);
        color: var(--error-color);
      }

      .progress-bar {
        width: 100%;
        height: 5px;
        background-color: #e0e0e0;
        border-radius: 3px;
        margin-top: 15px;
        overflow: hidden;
        display: none;
      }

      @media (min-width: 768px) {
        .progress-bar {
          height: 6px;
          margin-top: 20px;
        }
      }

      .progress {
        height: 100%;
        background-color: var(--primary-color);
        width: 0%;
        transition: width 0.3s ease;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
      }

      @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
      }

      .pulse {
        animation: pulse 1.5s infinite;
      }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
  </head>
  <body>
    <div class="upload-box">
      <h1>Upload Your Document</h1>
      <form method="POST" enctype="multipart/form-data" id="uploadForm">
        <div class="file-upload-wrapper">
          <label class="file-upload-label" id="fileUploadLabel">
            <i class="fas fa-cloud-upload-alt"></i>
            <span>Drag & drop your file here or</span>
            <span class="browse-text">Browse Files</span>
          </label>
          <input type="file" name="document" accept=".pdf,.doc,.docx,.csv,.xls,.xlsx" id="fileInput">
        </div>
        <p class="file-info" id="fileInfo"></p>
        <div class="progress-bar" id="progressBar">
          <div class="progress" id="progress"></div>
        </div>
        <input type="submit" value="Upload" id="submitBtn" disabled>
      </form>

      {% if filename %}
        <div class="status-message success">Uploaded: {{ filename }}</div>
      {% elif error %}
        <div class="status-message error">{{ error }}</div>
      {% endif %}
    </div>

    <script>
      const fileInput = document.getElementById('fileInput');
      const submitBtn = document.getElementById('submitBtn');
      const fileUploadLabel = document.getElementById('fileUploadLabel');
      const fileInfo = document.getElementById('fileInfo');
      const progressBar = document.getElementById('progressBar');
      const progress = document.getElementById('progress');
      const form = document.getElementById('uploadForm');

      // Format file size
      function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
      }

      // Handle file selection
      fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
          const file = fileInput.files[0];
          fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
          fileInfo.style.display = 'block';
          submitBtn.disabled = false;
          submitBtn.classList.add('pulse');
        } else {
          fileInfo.style.display = 'none';
          submitBtn.disabled = true;
          submitBtn.classList.remove('pulse');
        }
      });

      // Drag and drop functionality
      fileUploadLabel.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUploadLabel.style.borderColor = 'var(--primary-color)';
        fileUploadLabel.style.backgroundColor = 'var(--light-blue)';
      });

      fileUploadLabel.addEventListener('dragleave', () => {
        fileUploadLabel.style.borderColor = 'var(--border-color)';
        fileUploadLabel.style.backgroundColor = '#f1f8ff';
      });

      fileUploadLabel.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUploadLabel.style.borderColor = 'var(--border-color)';
        fileUploadLabel.style.backgroundColor = '#f1f8ff';
        
        if (e.dataTransfer.files.length) {
          fileInput.files = e.dataTransfer.files;
          fileInput.dispatchEvent(new Event('change'));
        }
      });

      // Form submission
      form.addEventListener('submit', (e) => {
        if (fileInput.files.length > 0) {
          submitBtn.value = "Uploading...";
          submitBtn.disabled = true;
          submitBtn.classList.remove('pulse');
          progressBar.style.display = 'block';
          
          // Simulate progress (in a real app, you'd use XMLHttpRequest or Fetch API)
          let progress = 0;
          const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
              progress = 100;
              clearInterval(interval);
            }
            document.getElementById('progress').style.width = progress + '%';
          }, 200);
        }
      });

      // Show status message if exists
      document.addEventListener('DOMContentLoaded', () => {
        const statusMessage = document.querySelector('.status-message');
        if (statusMessage) {
          setTimeout(() => {
            statusMessage.style.opacity = '0';
            statusMessage.style.transform = 'translateY(-10px)';
            setTimeout(() => {
              statusMessage.remove();
            }, 500);
          }, 5000);
        }
      });

      // Mobile-specific adjustments
      function handleMobileView() {
        if (window.innerWidth < 768) {
          // Additional mobile-specific adjustments if needed
        }
      }

      // Initialize and add resize listener
      handleMobileView();
      window.addEventListener('resize', handleMobileView);
    </script>
  </body>
</html>
'''

# ✅ Flask route for upload
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    filename = None
    error = None
    if request.method == 'POST':
        uploaded_file = request.files.get('document')
        print(f"[DEBUG] Upload attempt: {uploaded_file}")
        if uploaded_file and uploaded_file.filename != '':
            if is_allowed(uploaded_file.filename):
                safe_filename = secure_filename(uploaded_file.filename)
                save_path = UPLOAD_FOLDER / safe_filename
                try:
                    uploaded_file.save(save_path)
                    print(f"[✓] File uploaded: {save_path}")
                    filename = safe_filename
                except Exception as e:
                    error = f"❌ Failed to save file: {str(e)}"
                    print(error)
            else:
                error = "❌ File type not allowed!"
                print(error)
        else:
            error = "❌ No file selected!"
            print(error)
    return render_template_string(HTML_PAGE, filename=filename, error=error)

# ✅ QR Code generator
def generate_qr_and_open():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    url = f"http://{local_ip}:5000"
    img = qrcode.make(url)
    qr_path = "flask_qr.png"
    img.save(qr_path)
    print(f"[✓] QR Code Generated: {qr_path} | URL: {url}")
    time.sleep(1)
    try:
        os.startfile(qr_path)
    except:
        webbrowser.open(qr_path)

# ✅ Start Flask app with QR
if __name__ == '__main__':
    threading.Thread(target=generate_qr_and_open).start()
    app.run(host='0.0.0.0', port=5000)
