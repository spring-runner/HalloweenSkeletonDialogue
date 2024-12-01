import base64
import cv2
import logging
import os

# Number of frames to use to allow the camera to adjusts to the lighting conditions.
NUM_FRAMES_FOR_CAMERA_ADJUSTMENT = 1

class Camera:
    def __init__(self, log_file_path):
        self.__camera_port = 0
        self.__max_image_size = 360 # Maximum size of the image to send to the AI model.
        self.__image_log_file_base = log_file_path # Base name for the image log file.
        self.__images_taken = 0
        self.__camera = cv2.VideoCapture(0)
        if not self.__camera.isOpened():
            logging.error("Failed to open camera in initialization.")
            raise RuntimeError("Failed to open camera.")
        self.__camera_adjusted = False

    def __resize_image(self, image):
        """ Resize the image to make it faster / cheaper for the AI model to process."""
        height, width = image.shape[:2]
        if height > self.__max_image_size or width > self.__max_image_size:
            if height > width:
                scale = self.__max_image_size/ height
            else:
                scale = self.__max_image_size / width
            image = cv2.resize(image, (0,0), fx=scale, fy=scale)
        return image

    def __adjust_camera(self)->bool:
        """ Take a few pictures so the camera adjusts to the lighting conditions."""
        if self.__camera_adjusted:
            return True
        for i in range(NUM_FRAMES_FOR_CAMERA_ADJUSTMENT):
            self.__camera_adjusted, temp = self.__camera.read()
            if not self.__camera_adjusted:
                logging.error("Failed to read from camera.")
                break
        return self.__camera_adjusted

    def __get_image(self)->(bool, cv2.VideoCapture): # type: ignore
        """ Get an image from the camera."""
        if not self.__camera.isOpened():
            logging.error("Camera is not open.")
            return None, None
        if not self.__adjust_camera():
            logging.error("Failed to adjust camera.")
            return None, None
        retval, im = self.__camera.read()
        return retval, im

    def __convert_image_to_base64(self, image):
        """ Convert an image to a base64 string to send as data to the AI client."""
        buffer = cv2.imencode('.jpg', image)[1]
        jpg_as_bytes = base64.b64encode(buffer) 
        jpg_as_text = jpg_as_bytes.decode('utf-8')
        return f"data:image/jpeg;base64,{jpg_as_text}"
    
    def get_webcam_image(self)->cv2.VideoCapture:
        """ Get an image from the webcam.  Return a jpg."""
        logging.info("Taking a picture with the webcam.")
        status, image = self.__get_image()
        if status:
            self.__images_taken += 1
            image = self.__resize_image(image)
            filename = f'{self.__image_log_file_base}{self.__images_taken}.jpg'
            logging.info(f'Writing to {filename}.')
            if not cv2.imwrite(filename, image):
                logging.error(f"Failed to write image to {filename}.")
            return image
        else:
            logging.error("Failed to get image.")
            return None
    
    def get_webcam_image_as_base64(self)->str:
        """ Get an image from the webcam and return as a base64 string."""
        image = self.get_webcam_image()
        if image is None:
            return ""
        return self.__convert_image_to_base64(image)

    def __del__(self):
        self.__camera.release()


if __name__ == "__main__":
    if not os.path.exists("Logs"):
        os.makedirs("Logs")
    logging.basicConfig(filename=os.path.join("Logs", "camera-test.log"),
                        level=logging.INFO)

    camera = Camera(os.path.join("Logs", "image"))
    camera.get_webcam_image()
    del camera