from django.http import JsonResponse
from .models import UserData, Post, PostImage, CommentImage, PostComment
from django.contrib.auth.models import User
from .serializers import (
    user_serializer,
    post_serializer,
    post_image_serializer,
    user_data_serializer,
    comment_image_serializer,
    post_comment_serializer,
)
from rest_framework.response import Response
import rest_framework.status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError
import time

# здесь  написал передачу данных через тело строки, чтобы было проще скейлить обьемы данных на запрос
# реализованы все операции CRUD
user_feed_history = {}

user_history_critical_amount = 1000


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip_list = [ip.strip() for ip in x_forwarded_for.split(",")]
        ip = ip_list[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    # Валидация IP-адреса
    try:
        validate_ipv46_address(ip)
    except ValidationError:
        ip = None
    return ip


@api_view(["GET"])
def get_comments(request):
    try:
        start_amount = request.GET.get("start_amount", 0)
        post_id = request.GET.get("post_id", -1)
        amount = request.GET.get("amount", 0)
    except:
        post_id = -1
        amount = 0
        start_amount = 0
    print(start_amount, post_id, amount)
    post = get_object_or_404(Post, id=int(post_id))

    # Сохраняем результат запроса в переменную

    comments_queryset = post.comments.all().order_by("-created_at")

    print(comments_queryset)

    end_amount = min(comments_queryset.count(), int(start_amount) + int(amount))

    comments_data = post_comment_serializer(post.comments.all(), many=True).data[
        int(start_amount) : end_amount
    ]

    for comment in comments_data:
        comment_obj = post.comments.get(id=comment["id"])  # Получаем объект комментария
        comment_images = comment_image_serializer(
            comment_obj.images.all(), many=True
        ).data
        print(comment["author"])
        user_obj = user_serializer(User.objects.get(id=comment["author"])).data

        comment["images"] = comment_images  # Добавляем изображения в поле 'images'
        comment["user"] = user_obj
    # Теперь comments_data содержит комментарии с изображениями
    return JsonResponse(comments_data, safe=False)


@api_view(["GET", "POST"])
def posts(request):
    if request.method == "GET":
        start_time = time.time()
        amount = int(request.GET.get("amount", 10))
        try:
            last_posts = str(request.GET.get("last_posts", [])).split(",")
        except Exception as e:
            print(e)
            last_posts = []
        if last_posts == ["[]"]:
            last_posts = []
        client_ip = get_client_ip(request)

        try:
            user_feed_history[client_ip] += last_posts
        except:
            user_feed_history[client_ip] = last_posts

        if amount < 0:
            return Response(
                "negative indexing not supported",
                status=rest_framework.status.HTTP_400_BAD_REQUEST,
            )

        requested_posts = Post.objects.exclude(
            id__in=user_feed_history[client_ip]
        ).order_by("-created_at")

        if len(requested_posts) > amount:
            requested_posts = requested_posts[:amount]
        else:
            user_feed_history[client_ip] = []

        if len(user_feed_history[client_ip]) > user_history_critical_amount:
            user_feed_history[client_ip] = user_feed_history[client_ip][
                len(user_feed_history[client_ip]) - user_history_critical_amount :
            ]

        serializer = post_serializer(requested_posts, many=True)
        print("task done in " + str(time.time() - start_time) + "seconds")
        return JsonResponse(serializer.data, safe=False)
    elif request.method == "POST":
        serializer = post_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                "data added successfully", status=rest_framework.status.HTTP_201_CREATED
            )
        else:
            return Response(
                "invalid data", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )


@api_view(["POST"])
def auth(request):
    login = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=login, password=password)

    print(login, password)

    if user is not None:
        serializer = user_serializer(user, many=False)
        user_data = user_data_serializer(user.data, many=False)
        return JsonResponse(
            {
                "successful": True,
                "user_info": serializer.data,
                "user_data": user_data.data,
            },
            safe=False,
        )
    else:
        return JsonResponse({"successful": False})


@api_view(["GET", "PUT", "DELETE"])
def images_detail(request):
    image = get_object_or_404(PostImage, id=int(request.GET.get("request_id")))
    if request.method == "GET":
        serializer = post_image_serializer(image, many=False)
        return JsonResponse(serializer.data, safe=False)
    if request.method == "PUT":
        serializer = post_image_serializer(image, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                "data updated successfully", status=rest_framework.status.HTTP_200_OK
            )
        else:
            return Response(
                "invalid data", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )
    if request.method == "DELETE":
        image.delete()
        return Response(
            "data deleted successfully", status=rest_framework.status.HTTP_200_OK
        )


@api_view(["GET", "PUT", "DELETE"])
def users_detail(request):
    user = get_object_or_404(User, id=int(request.GET.get("request_id")))
    if request.method == "GET":
        serializer = user_serializer(user, many=False)
        user_data = user_data_serializer(user.data, many=False)
        images = post_serializer(user.posts.all(), many=True)
        return JsonResponse(
            {
                "user_info": serializer.data,
                "user_extra_data": user_data.data,
                "posts": images.data,
            },
            safe=False,
        )
    if request.method == "PUT":
        serializer = user_serializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                "data updated successfully", status=rest_framework.status.HTTP_200_OK
            )
        else:
            return Response(
                "invalid data", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )
    if request.method == "DELETE":
        user.delete()
        return Response(
            "data deleted successfully", status=rest_framework.status.HTTP_200_OK
        )


@api_view(["GET", "PUT", "DELETE"])
def posts_detail(request):
    post = get_object_or_404(Post, id=int(request.GET.get("request_id")))
    if request.method == "GET":
        serializer = post_serializer(post, many=False)
        images = post_image_serializer(post.images.all(), many=True)
        author = user_serializer(post.author, many=False)
        return JsonResponse(
            {
                "post_info": serializer.data,
                "images": images.data,
                "author": author.data,
            },
            safe=False,
        )
    if request.method == "PUT":
        serializer = post_serializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                "data updated successfully", status=rest_framework.status.HTTP_200_OK
            )
        else:
            return Response(
                "invalid data", status=rest_framework.status.HTTP_400_BAD_REQUEST
            )
    if request.method == "DELETE":

        post.delete()
        return Response(
            "data deleted successfully", status=rest_framework.status.HTTP_200_OK
        )
