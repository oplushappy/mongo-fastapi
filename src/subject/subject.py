
import datetime
import os

import string
import pymongo
from bson import ObjectId
from fastapi import APIRouter, Body, Request, Response, HTTPException, status, UploadFile, Form, middleware, FastAPI
from fastapi.encoders import jsonable_encoder
from typing import List
import uuid

from subject.model import Subject, Video, UserPersonalData
from subject.method import *

# app = FastAPI()
router = APIRouter()

from bson.objectid import ObjectId


# still not test
@router.post("/user_personal", response_description="user personal data",status_code=status.HTTP_201_CREATED)
def create_user(request: Request, information: UserPersonalData = Form()):
    information = form_change_to_json(information)
    user = {
        "full_name": information["name"],
        "gender": information["gender"],
        "age": information["age"],
        "email": information["email"]
    }
    new_user = request.app.db.users.find_one_and_update({"_id" : request.state.id},{ "$set": {user} })
    return new_user

#列出測試者所有影片
@router.get("/list/video",response_model=List[Video], response_description="list all video about subject",status_code=status.HTTP_200_OK)
def list_video(request: Request):
    video_list = request.app.db.video.find({"user_id": request.state.id}, limit=100).sort("date", pymongo.ASCENDING)
    res_video_list = []
    for video in video_list:
        video["video_id"] = str(video["_id"])
        del video["thumbnail_path"]
        video["thumbnail_url"] = "subject/thumbnail?video_id=" + video["video_id"] 
        res_video_list.append(Video(**video))
    return res_video_list

@router.get("/thumbnail/")
def generate(request:Request, video_id: str):
    video = request.app.db.video.find_one({"_id": ObjectId(video_id)})
    if video == None:
        return status.HTTP_404_NOT_FOUND
    if os.path.isfile(video["thumbnail_path"]) == False:
        raise HTTPException(status_code=404, detail="thumbnail not found")
    with open(video["thumbnail_path"], "rb") as read_thumbnail:
        return Response(content=read_thumbnail.read(), media_type="image/jpeg")

#修改影片
@router.put("/update/video",response_model = Video, response_description="do some change in video",status_code=status.HTTP_200_OK)
def update_video(request: Request, information: str = Form()):#video_id: str, date: datetime.date, location: str
    information = form_change_to_json(information)
    updated_video = request.app.db.video.find_one_and_update(
        {"_id": ObjectId(information["video_id"])},
        {"$set": {"subject":information["name"],
                    "gender":information["gender"],
                    "detect":information["detect"],
                    "date": information["date"], 
                    "location": information["location"]}},
        upsert=True
    )
    updated_video["video_id"] = str(updated_video["_id"])
    return Video(**updated_video)

#刪除影片紀錄
@router.delete("/delete/video", response_description="Delete a video",status_code=status.HTTP_202_ACCEPTED)
def delete_video(request: Request, video_id: str):
    delete_result = request.app.db.video.find_one_and_delete({
        "user_id": request.state.id,
        "_id": ObjectId(video_id)
    })
    if delete_result:
        return status.HTTP_202_ACCEPTED
    raise HTTPException(status_code=404, detail="video not exist")

