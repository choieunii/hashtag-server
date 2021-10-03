import math
from dbr import *
# 직선거리 기반 트랙커


class EuclideanDistTracker:
    def __init__(self):
        # 객체의 중심 위치 저장
        # {(class,id):(cx, cy)}
        self.all_center_points = {}
        self.all_barcode_info = {}
        self.all_product_info = {}
        # 아이디의 개수 카운팅
        # self.id_count = 0
        # 0 : barcode/ 1 : product
        self.reader = BarcodeReader()

        license_key = "t0072fQAAAAgRqqnjS+UaXWzx01E7MLbP+BWb0H4C7quLjMqPzDLDzoI2zN0noPeAOS/bVXJCXiX4UBYppedid9AUQ/ZzawqynBt9"
        self.reader.init_license(license_key)
        self.decode_data = []
        self.class_ids = {0: 0, 1: 0}

    def isInside(self, barcode, product):
        codex, codey, codew, codeh = barcode
        prox, proy, prow, proh = product

        if prox <= codex and proy <= codey and codex + codew <= prox + prow and codey + codeh <= proy + proh:
            return True
        else:
            return False

    def decodeframe(self, frame, left, top, right, bottom):
        settings = self.reader.reset_runtime_settings()
        settings = self.reader.get_runtime_settings()
        settings.region_bottom = bottom
        settings.region_left = left
        settings.region_right = right
        settings.region_top = top
        # settings.barcode_format_ids = EnumBarcodeFormat.BF_QR_CODE
        # settings.expected_barcodes_count = 1
        # 지정된 JSON 파일의 설정으로 런타임 설정 update
        self.reader.update_runtime_settings(settings)

        try:
            # 정의 된 형식의 이미지 픽셀을 포함하는 메모리 버퍼에서 바코드를 디코딩
            text_results = self.reader.decode_buffer(frame)
            if text_results != None:
                for text_result in text_results:
                    self.decode_data.append(text_result.barcode_text)
            return text_results  # 있으면 결과
        except BarcodeReaderError as bre:
            print(bre)  # 예외처리

        return None

    def update(self, classes, bboxes, frame):
        # object의 bbox와 class_id정보
        objects_bbs_cids = []

        # bbox = [x,y,w,h] 정보 포함
        # one_class = 0 or 1
        for one_class, bbox in zip(classes, bboxes):
            x, y, w, h = bbox
            # 중심 x,y값 계산
            cx = (x+x+w)//2
            cy = (y+y+h)//2
            one_class = int(one_class)

            # 이전에 이미 인식된 객체인지 확인
            same_object = False
            # items() : (key, value)반환
            # 모든 이미 존재하는 객체와 거리를 계산해
            # center_points = {(int(class),id):(cx, cy),...}
            # class_id = (class,id) / pt = (cx, cy)
            for class_id, pt in self.all_center_points.items():
                # 같은 객체인 경우 거리 측정 / 다른 객체면 pass
                if one_class == class_id[0]:
                    # dist : 현재 객체의 중심점과 이전 프레임에 인식된 (모든)객체의 중심점 직선 거리
                    dist = math.hypot(cx-pt[0], cy-pt[1])

                    # 거리가 25이하이면 id 객체 중심 위치 업데이트
                    if dist < 100:
                        self.all_center_points[class_id] = (x, y, w, h)
                        if class_id[0] == 0:
                            result = self.decodeframe(
                                frame, x, y, (x+w), (y+h))
                            if result is not None:
                                self.all_barcode_info[(class_id)] = (
                                    x, y, w, h, result[0].barcode_text)
                                objects_bbs_cids.append(
                                    [x, y, w, h, class_id, result[0].barcode_text])
                            else:
                                objects_bbs_cids.append(
                                    [x, y, w, h, class_id, " "])

                        else:
                            flag = False
                            for barcode in self.all_barcode_info:
                                barx, bary, barw, barh, info = self.all_barcode_info[barcode]
                                if self.isInside((barx, bary, barw, barh), (x, y, w, h)):
                                    self.all_product_info[(class_id)] = (
                                        (x, y, w, h), info)
                                    flag = True
                                    objects_bbs_cids.append(
                                        [x, y, w, h, class_id, info])
                            if(not flag):
                                self.all_product_info[(class_id)] = (
                                    x, y, w, h)
                                objects_bbs_cids.append(
                                    [x, y, w, h, class_id, " "])

                        # 기존에 있던 객체임을 표시
                        same_object = True
                        break
                # else class가 다를때 처리:
                # 거리, 위치? 바코드 center값이 상품 영역 안에 있으면 연관
                # {(class,id):(cx, cy)} > {(class,id):(bbox(x,y,w,h), decoding한 barcode정보)}
                # barcode/product 모두 인식 ID할당 정보를 계속 축적 둘다 트래킹
                # product에 barcode 정보를 저장하게 되면, barcode에 대한 트래킹 계속 해야되는 걸까?
                # 왜냐면 barcode 인식되서 디코딩이 되서 product에 저장이
                # 위에서 비교를 할때는 barcode 정보는 사용하지 않아.
                # 해당 바코드 정보가 product에 할당이 되는 경우에 그 바코드 정보는 따로 변수에 저장 안해도 될것 같음.

            # 넣고 빼고 barcode에 대한 처리 안해줌.
            # {(class,id):(bbox(x,y,w,h), decoding한 barcode정보)}
            # center값 계산
            # (0~x1) - f1 / (x1~x2) - f2/ (x2~x3) - f3 안/밖 판단
            # product class에 대해서만 처리

            # 새로운 객체가 감지된 경우
            if same_object is False:
                new_class_id = (one_class, self.class_ids[one_class])
                self.all_center_points[(new_class_id)] = (x, y, w, h)
                if new_class_id[0] == 0:
                    result = self.decodeframe(frame, x, y, (x+w), (y+h))
                    if result is not None:
                        self.all_barcode_info[(new_class_id)] = (
                            x, y, w, h, result[0].barcode_text)
                        objects_bbs_cids.append(
                            [x, y, w, h, new_class_id, result[0].barcode_text])
                    else:
                        objects_bbs_cids.append(
                            [x, y, w, h, new_class_id, " "])
                else:
                    flag = False
                    for barcode in self.all_barcode_info:
                        barx, bary, barw, barh, info = self.all_barcode_info[barcode]
                        if self.isInside((barx, bary, barw, barh), (x, y, w, h)):
                            self.all_product_info[(new_class_id)] = (
                                (x, y, w, h), info)
                            objects_bbs_cids.append(
                                [x, y, w, h, new_class_id, info])
                            flag = True
                    if(not flag):
                        self.all_product_info[(new_class_id)] = (
                            x, y, w, h)
                        objects_bbs_cids.append(
                            [x, y, w, h, new_class_id, " "])
                self.class_ids[one_class] += 1

        print(self.all_product_info)
        print(self.all_barcode_info)
        # 없어진 객체 제거 (최신화)
        # new_center_points = {}
        # for object_bb_cid in objects_bbs_cids:
        #     _, _, _, _, object_cid = object_bb_cid
        #     # x, y, w, h, object_id = object_bb_id
        #     center = self.center_points[object_cid]
        #     new_center_points[object_cid] = center
        # self.center_points = new_center_points.copy()

        # objects_bbs_cids = []
        return objects_bbs_cids
