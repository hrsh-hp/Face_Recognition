from django.http import JsonResponse,HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import *

#for face recogniton
import face_recognition
import base64
import cv2
from PIL import Image
import numpy as np
from io import BytesIO

# Function to load the known faces for now it's manual process
# def load_known_faces():
#     known_faces = {}
    
#     name_paths = [
#         ("Harsh","static/images/Harsh.jpeg"),
#         ("Gautam","static/images/Gautam.jpeg"),
#         ("Dipen","static/images/Dipen.jpeg"),
#     ]
    
#     for name, file in name_paths:
#         image = face_recognition.load_image_file(file)
#         face_encoding = face_recognition.face_encodings(image)[0]
#         known_faces[name] = face_encoding
        
#     # print(known_faces)
#     return known_faces

# known_faces = load_known_faces()

# Face Recognition view 
@csrf_exempt
def recognize_face(request):
    # print(known_faces)
    if request.method == "POST":
        try:
            # decoding the base64 received from frontend into image
            image_data = request.POST.get('imageData')
            img_data = base64.b64decode(image_data.split(',')[1])
            image = Image.open(BytesIO(img_data))
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # getting face encodings from received image
            rec_face_locations = face_recognition.face_locations(frame, number_of_times_to_upsample=2)
            rec_face_encodings = face_recognition.face_encodings(frame,rec_face_locations)
         
            recognized_name = []
            name = "Unknown!!"

            #comparing known face encodings with received face encodings
            for rec_face_encoding in rec_face_encodings:
                
                #Getting the known faces from database
                known_faces = {}
                for face_obj in KnownFace.objects.all():
                    known_image_data = base64.b64decode(face_obj.image.split(',')[1])
                    known_image = Image.open(BytesIO(known_image_data))
                    known_faces[face_obj.name] = face_recognition.face_encodings(np.array(known_image))[0]
            

                matches = face_recognition.compare_faces(list(known_faces.values()), rec_face_encoding)
                
                if True in matches:
  
                    first_match_index = matches.index(True)
                    name = list(known_faces.keys())[first_match_index]
                    print(f"Welcome {name}")
                    recognized_name.append(name)
                    
                else :
                    print('face not matches')
                    
            print(recognized_name)
            # Convert a frame in to Jpeg
            _ , jpeg = cv2.imencode('.jpeg', frame)
            res_img = jpeg.tobytes()  
            response = base64.b64encode(res_img).decode('utf-8') 
            return JsonResponse({'name':name,'image':response})
                    
        except Exception as e:
            print(e)
            return JsonResponse({'err':str(e)})
        
    else:
        print('not a Post method')
        return JsonResponse({'err':"Invalid request method it must be POST"})

def index(request):
    return render(request, 'Auth/index.html')