import re

from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .bedrock import *
from .serializers import *
from .redis import *

class CallBedrockAllPlatform(APIView):

    """
    주어진 user_id와 date를 기반으로 Calendar 데이터를 조회한 뒤 Bedrock 모델 호출
    """

    def post(self, request, date):
        """
        URL로부터 date 값을 직접 받도록 수정
        """
        try:
            # 로그인된 사용자 ID 가져오기
            auth_user = request.user
            user_id = getattr(auth_user, "username", None)  # Cognito의 user_id

            if not user_id:
                return Response({"error": "User ID is required or unauthorized."}, 
                             status=status.HTTP_401_UNAUTHORIZED)

            # 날짜 형식 확인
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                target_date_str = target_date.strftime("%Y-%m-%d")
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, 
                             status=status.HTTP_400_BAD_REQUEST)

            # Calendar에서 user_id로 데이터 조회
            calendar = Calendar.objects(user_id=user_id).first()
            if not calendar or not calendar.entries:
                return Response({"error": "No entries found for the given user_id."}, 
                             status=status.HTTP_404_NOT_FOUND)

            # 해당 날짜의 데이터 조회
            entry = calendar.entries.get(target_date_str)
            if not entry:
                return Response({"error": f"No entry found for date {target_date_str}."}, 
                             status=status.HTTP_404_NOT_FOUND)

            # emoticons 데이터 추출
            emoticons = entry.emoticons
            if not emoticons:
                return Response({"error": "No emoticons data available in the entry."}, 
                             status=status.HTTP_400_BAD_REQUEST)

            # EmoticonsSerializer로 직렬화
            emoticons_serializer = EmoticonsSerializer(emoticons)
            emoticons_data = emoticons_serializer.data

            # Diary 데이터 포함
            diary_text = entry.diary or "No diary provided"

            # Bedrock 호출
            input_text = f"Emoticons Details: {emoticons_data}, Diary: {diary_text}"
            bedrock_response_data = bedrock_response_all_platform(input_text)

            # Bedrock 응답에서 추천 콘텐츠 제목 추출
            recommended_content = None
            try:
                last_line = bedrock_response_data.strip().split("\n")[-1]
                print(f"Bedrock 응답 마지막 줄: {last_line}")

                if last_line.startswith("추천 콘텐츠"):
                    prefix = "추천 콘텐츠"
                    # "추천 콘텐츠" 다음에 오는 공백 또는 콜론(:)을 처리
                    content_after_prefix = re.sub(r'^추천 콘텐츠\s*[:\s]*', '', last_line)
                    # 첫 번째 공백을 기준으로 플랫폼과 콘텐츠 분리
                    platform, _, content = content_after_prefix.partition(" ")
                    recommended_content = content.strip().strip('"').strip("'")
                    print(f"추출된 콘텐츠 제목: {recommended_content}")
                elif last_line.startswith("추천 컨텐츠"):
                    prefix = "추천 컨텐츠"
                    # "추천 콘텐츠" 다음에 오는 공백 또는 콜론(:)을 처리
                    content_after_prefix = re.sub(r'^추천 콘텐츠\s*[:\s]*', '', last_line)
                    # 첫 번째 공백을 기준으로 플랫폼과 콘텐츠 분리
                    platform, _, content = content_after_prefix.partition(" ")
                    recommended_content = content.strip().strip('"').strip("'")
                    print(f"추출된 콘텐츠 제목: {recommended_content}")
            except Exception as e:
                print(f"콘텐츠 제목 추출 중 오류: {str(e)}")

            # Entry에 Bedrock 응답 및 영화 제목 저장
            entry.result_emotion = bedrock_response_data
            entry.recommend_content = recommended_content
            calendar.entries[target_date_str] = entry
            calendar.save()

            # ContentEmotionStats에 감정 통계 저장
            if recommended_content and recommended_content.strip() and calendar.mbti:
                try:
                    # 콘텐츠 통계 데이터 가져오기 또는 생성
                    content_stats = ContentEmotionStats.objects(title=recommended_content).first()
                    if not content_stats:
                        content_stats = ContentEmotionStats(title=recommended_content)
                        content_stats.save()
                        print(f"새로운 콘텐츠 통계 생성: {recommended_content}")

                    # emoticons 데이터에서 emotion 리스트 가져오기
                    emotions = emoticons_data.get('emotion', [])
                    if emotions:
                        # 감정 데이터 추가
                        content_stats.add_emotions(calendar.mbti, emotions)
                        print(f"감정 통계 추가 완료: 콘텐츠={recommended_content}, MBTI={calendar.mbti}, 감정={emotions}")
                except Exception as e:
                    print(f"감정 통계 저장 중 오류 발생: {str(e)}")
            else:
                print(f"데이터 저장 조건 불충족: recommended_content={recommended_content}, mbti={calendar.mbti}")



            # 응답 데이터 구성
            response_data = {
                "bedrock_response": bedrock_response_data,
                "recommended_content": recommended_content,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(f"API 처리 중 오류 발생: {error_message}")
            return Response({"error": error_message}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CallBedrockSubPlatform(APIView):

    """
    주어진 user_id와 date를 기반으로 Calendar 데이터를 조회한 뒤 Bedrock 모델 호출
    """

    def post(self, request, date):
        """
        URL로부터 date 값을 직접 받도록 수정
        """
        try:
            # 로그인된 사용자 ID 가져오기
            auth_user = request.user
            user_id = getattr(auth_user, "username", None)  # Cognito의 user_id

            if not user_id:
                return Response({"error": "User ID is required or unauthorized."},
                             status=status.HTTP_401_UNAUTHORIZED)

            # 날짜 형식 확인
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                target_date_str = target_date.strftime("%Y-%m-%d")
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."},
                             status=status.HTTP_400_BAD_REQUEST)

            # Calendar에서 user_id로 데이터 조회
            calendar = Calendar.objects(user_id=user_id).first()
            if not calendar or not calendar.entries:
                return Response({"error": "No entries found for the given user_id."},
                             status=status.HTTP_404_NOT_FOUND)

            # 해당 날짜의 데이터 조회
            entry = calendar.entries.get(target_date_str)
            if not entry:
                return Response({"error": f"No entry found for date {target_date_str}."},
                             status=status.HTTP_404_NOT_FOUND)

            # emoticons 데이터 추출
            emoticons = entry.emoticons
            if not emoticons:
                return Response({"error": "No emoticons data available in the entry."},
                             status=status.HTTP_400_BAD_REQUEST)

            # 추가적인 Calendar 데이터(`subscribe_platform`, `mbti`) 가져오기
            subscribe_platform = calendar.subscribe_platform or "No platform subscribed"
            mbti = calendar.mbti or "MBTI not provided"

            # EmoticonsSerializer로 직렬화
            emoticons_serializer = EmoticonsSerializer(emoticons)
            emoticons_data = emoticons_serializer.data

            # Diary 데이터 포함
            diary_text = entry.diary or "No diary provided"

            # Bedrock 호출
            input_text = f"Emoticons Details: {emoticons_data}, Diary: {diary_text}, " \
                         f"Subscribed Platform: {subscribe_platform}"
            bedrock_response_data = bedrock_response_sub_platform(input_text)

            # Bedrock 응답에서 추천 콘텐츠 제목 추출
            recommended_content = None
            try:
                last_line = bedrock_response_data.strip().split("\n")[-1]
                print(f"Bedrock 응답 마지막 줄: {last_line}")

                if last_line.startswith("추천 콘텐츠"):
                    prefix = "추천 콘텐츠"
                    # "추천 콘텐츠" 다음에 오는 공백 또는 콜론(:)을 처리
                    content_after_prefix = re.sub(r'^추천 콘텐츠\s*[:\s]*', '', last_line)
                    # 첫 번째 공백을 기준으로 플랫폼과 콘텐츠 분리
                    platform, _, content = content_after_prefix.partition(" ")
                    recommended_content = content.strip().strip('"').strip("'")
                    print(f"추출된 콘텐츠 제목: {recommended_content}")
                elif last_line.startswith("추천 컨텐츠"):
                    prefix = "추천 컨텐츠"
                    # "추천 콘텐츠" 다음에 오는 공백 또는 콜론(:)을 처리
                    content_after_prefix = re.sub(r'^추천 콘텐츠\s*[:\s]*', '', last_line)
                    # 첫 번째 공백을 기준으로 플랫폼과 콘텐츠 분리
                    platform, _, content = content_after_prefix.partition(" ")
                    recommended_content = content.strip().strip('"').strip("'")
                    print(f"추출된 콘텐츠 제목: {recommended_content}")
            except Exception as e:
                print(f"콘텐츠 제목 추출 중 오류: {str(e)}")

            # Entry에 Bedrock 응답 및 영화 제목 저장
            entry.result_emotion = bedrock_response_data
            entry.recommend_content = recommended_content
            calendar.entries[target_date_str] = entry
            calendar.save()

            # ContentEmotionStats에 감정 통계 저장
            if recommended_content and recommended_content.strip() and calendar.mbti:
                try:
                    # 콘텐츠 통계 데이터 가져오기 또는 생성
                    content_stats = ContentEmotionStats.objects(title=recommended_content).first()
                    if not content_stats:
                        content_stats = ContentEmotionStats(title=recommended_content)
                        content_stats.save()
                        print(f"새로운 콘텐츠 통계 생성: {recommended_content}")

                    # emoticons 데이터에서 emotion 리스트 가져오기
                    emotions = emoticons_data.get('emotion', [])
                    if emotions:
                        # 감정 데이터 추가
                        content_stats.add_emotions(calendar.mbti, emotions)
                        print(f"감정 통계 추가 완료: 콘텐츠={recommended_content}, MBTI={calendar.mbti}, 감정={emotions}")
                except Exception as e:
                    print(f"감정 통계 저장 중 오류 발생: {str(e)}")
            else:
                print(f"데이터 저장 조건 불충족: recommended_content={recommended_content}, mbti={calendar.mbti}")



            # 응답 데이터 구성
            response_data = {
                "bedrock_response": bedrock_response_data,
                "recommended_content": recommended_content,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(f"API 처리 중 오류 발생: {error_message}")
            return Response({"error": error_message},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuestionView(APIView):
    def post(self, request):
        # 요청 데이터 디버깅
        print("Request data received:", request.data)

        # 요청 데이터 검증을 위해 QuestionSerializer 사용
        serializer = QuestionSerializer(data=request.data)

        if serializer.is_valid():
            # 검증된 데이터를 ChatBot 함수로 전달
            question_text = serializer.validated_data.get("question_text")

            # Bedrock 모델 호출
            try:
                response_content = bedrock_chat_bot(input_text=question_text)
            except Exception as e:
                return Response(
                    {"error": f"ChatBot invocation failed: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # 성공적으로 ChatBot 응답 반환
            return Response({"response": response_content}, status=status.HTTP_200_OK)

        # 유효하지 않은 데이터가 입력된 경우
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BedrockResponseView(APIView):
    """
    특정 사용자 ID(user_id)와 특정 날짜(date)에 해당하는 Calendar 데이터를 조회
    """

    def get(self, request, date, user_id=None):
        # 날짜 형식 확인 및 파싱
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Please use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 사용자 정보 확인 (인증된 사용자 또는 제공된 사용자 ID)
        auth_user = request.user
        user_id = user_id or getattr(auth_user, "username", None)  # Cognito 사용 시 `username` 사용 가능

        if not user_id:
            return Response(
                {"error": "User ID is required or you are not authorized."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # 사용자 ID로 Calendar 검색
            calendar = Calendar.objects(user_id=user_id).first()  # 첫 번째 매칭 항목 가져오기

            if not calendar:
                return Response(
                    {"error": f"Calendar not found for user ID {user_id}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # entries에서 해당 날짜 확인
            target_date_str = target_date.strftime("%Y-%m-%d")  # 문자열로 변환
            entry = calendar.entries.get(target_date_str)  # 날짜 데이터 검색

            if not entry:
                return Response(
                    {"error": f"No entry found for the specified date: {target_date_str}."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # entry 데이터를 직렬화하여 응답
            serializer = RecommendSerializer(entry)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecommendContentView(APIView):
    """
    특정 사용자 ID(user_id)와 특정 날짜(date)에 해당하는 recommend_content와 매칭되는 콘텐츠 정보 조회
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, date, user_id=None):
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식을 사용하세요."},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_user = request.user
        user_id = user_id or getattr(auth_user, "username", None)

        if not user_id:
            return Response(
                {"error": "사용자 ID가 필요하거나 인증되지 않았습니다."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            calendar = Calendar.objects(user_id=user_id).first()
            if not calendar:
                return Response(
                    {"error": f"해당 사용자의 캘린더를 찾을 수 없습니다: {user_id}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            target_date_str = target_date.strftime("%Y-%m-%d")
            entry = calendar.entries.get(target_date_str)
            if not entry:
                return Response(
                    {"error": f"해당 날짜의 데이터를 찾을 수 없습니다: {target_date_str}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # recommend_content 값 가져오기
            recommend_content = entry.recommend_content
            if not recommend_content:
                return Response(
                    {"error": "추천 콘텐츠가 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Contents 컬렉션에서 매칭되는 콘텐츠 찾기
            # 정규식 패턴 생성 (^는 문자열의 시작을 의미)
            pattern = f"^{re.escape(recommend_content)}"
            content = Contents.objects(title__regex=pattern).first()

            if not content:
                return Response(
                    {"error": f"매칭되는 콘텐츠를 찾을 수 없습니다: {recommend_content}"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # ContentsSerializer를 사용하여 데이터 직렬화
            content_serializer = ContentsSerializer(content)
            response_data = {
                "recommend_content": recommend_content,
                "content_info": {
                    "title": content_serializer.data.get('title'),
                    "poster_url": content_serializer.data.get('poster_url')
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatSaveView(APIView):
    """
    View to save chat data to Redis
    """

    def post(self, request):
        serializer = ChatSerializer(data=request.data)

        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            user_message = serializer.validated_data['message']
            bot_response = serializer.validated_data['response']

            # Redis에 대화 내용 저장
            save_chat_to_redis(user_id, user_message, bot_response)

            return JsonResponse({"message": "Chat saved successfully."}, status=status.HTTP_200_OK)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatHistoryView(APIView):
    """
    View to retrieve chat history from Redis
    """

    def get(self, request, user_id):
        try:
            # Redis에서 대화 기록 가져오기
            chat_history = get_chat_history_from_redis(user_id)

            if not chat_history:
                return JsonResponse({"message": "No chat history found."}, status=status.HTTP_404_NOT_FOUND)

            return JsonResponse({"chat_history": chat_history}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)