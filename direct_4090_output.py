#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import cv2

# Force use of 4090 (GPU 1)
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

# Bypass X - write directly to framebuffer
print("Starting direct output to 4090 HDMI...")

# Create test image
img = np.zeros((1080, 1920, 3), np.uint8)
img[:] = (0, 100, 0)  # Green screen to confirm it's working
cv2.putText(img, "4090 DIRECT OUTPUT", (500, 540), 
            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)

# Save as image first
cv2.imwrite('/tmp/avatar_test.png', img)

# Use nvidia's direct framebuffer output
subprocess.run(['nvidia-settings', '-a', 'GPUCurrentClockFreqs=1'])

# Alternative: Use DRM/KMS direct output (no X needed)
print("Check your HDMI monitor - should show green screen")
EOFcat > direct_4090_output.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import cv2

# Force use of 4090 (GPU 1)
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

# Bypass X - write directly to framebuffer
print("Starting direct output to 4090 HDMI...")

# Create test image
img = np.zeros((1080, 1920, 3), np.uint8)
img[:] = (0, 100, 0)  # Green screen to confirm it's working
cv2.putText(img, "4090 DIRECT OUTPUT", (500, 540), 
            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)

# Save as image first
cv2.imwrite('/tmp/avatar_test.png', img)

# Use nvidia's direct framebuffer output
subprocess.run(['nvidia-settings', '-a', 'GPUCurrentClockFreqs=1'])

# Alternative: Use DRM/KMS direct output (no X needed)
print("Check your HDMI monitor - should show green screen")
EOFcat > direct_4090_output.py << 'EOF'
#!/usr/bin/env python3
import os
import subprocess
import numpy as np
import cv2

# Force use of 4090 (GPU 1)
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

# Bypass X - write directly to framebuffer
print("Starting direct output to 4090 HDMI...")

# Create test image
img = np.zeros((1080, 1920, 3), np.uint8)
img[:] = (0, 100, 0)  # Green screen to confirm it's working
cv2.putText(img, "4090 DIRECT OUTPUT", (500, 540), 
            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)

# Save as image first
cv2.imwrite('/tmp/avatar_test.png', img)

# Use nvidia's direct framebuffer output
subprocess.run(['nvidia-settings', '-a', 'GPUCurrentClockFreqs=1'])

# Alternative: Use DRM/KMS direct output (no X needed)
print("Check your HDMI monitor - should show green screen")
