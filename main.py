import os
import json
from collections import defaultdict
from datetime import datetime
from PIL import Image
import re
import sys
import msvcrt

def extract_extra_info_from_png(file_path):
    image = Image.open(file_path)
    exif_data = image.info['Description']
    extra_info = json.loads(str(exif_data))
    return extra_info

def parse_needed_data(extra_info):
    parsed_data = {
        "author": extra_info["author"],
        "world": extra_info["world"],
        "players": extra_info["players"]
    }
    return parsed_data

def process_folder(folder_path):
    png_files = [f for f in os.listdir(folder_path) if f.endswith('.png')]
    data_by_date = defaultdict(lambda: defaultdict(list))

    for png_file in png_files:
        file_path = os.path.join(folder_path, png_file)
        try:
            date_str = png_file.split('_')[1]
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            extra_info = extract_extra_info_from_png(file_path)
            parsed_data = parse_needed_data(extra_info)
            world_id = parsed_data['world']['id']
            data_by_date[date][world_id].append((file_path, parsed_data))
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    return data_by_date

def generate_html(data_by_date, output_file):
    html_content = """
    <html>
    <head>
        <title>VRChat Image Data</title>
        <style>
            .image-container { display: flex; flex-wrap: wrap; gap: 5px; }
            .image-item { flex: 1 1 calc(33.33% - 10px); display: flex; flex-direction: column; align-items: center; margin-bottom: 10px; }
            .image-item img { width: 100%; height: auto; cursor: pointer; }
            .image-item span { font-size: 14px; text-align: center; }
            .fullscreen { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.9); justify-content: center; align-items: center; z-index: 1000; flex-direction: column; color: white; box-sizing: border-box; }
            .fullscreen .container { display: flex; flex-direction: column; flex-grow: 1; overflow: hidden; }
            .fullscreen .container img { flex-grow: 1; max-width: 100%; max-height: 100%; object-fit: contain; }
            .fullscreen .header { margin-bottom: 10px; flex-shrink: 0; }
            .fullscreen .header h2 { margin-top: 10px; margin-bottom: 0px; }
            .fullscreen .header h3 { margin: 0; }
            .fullscreen .footer { margin-top: 10px; font-size: 16px; flex-shrink: 0; }
        </style>
        <script>
            let currentIndex = -1;
            let imageList = [];
            let worldList = [];
            let dateList = [];
            let totalImages = 0;

            function showFullscreen(src, index, world, link, dateStr, total) {
                const fullscreenDiv = document.getElementById('fullscreen');

                fullscreenDiv.style.display = 'flex';
                currentIndex = index;
                totalImages = total;
                updateFullscreenImage()
            }

            function hideFullscreen() {
                const fullscreenDiv = document.getElementById('fullscreen');
                fullscreenDiv.style.display = 'none';
            }

            function showNextImage() {
                if (currentIndex < imageList.length - 1) {
                    currentIndex++;
                    updateFullscreenImage();
                }
            }

            function showPrevImage() {
                if (currentIndex > 0) {
                    currentIndex--;
                    updateFullscreenImage();
                }
            }

            function updateFullscreenImage() {
                const fullscreenImg = document.getElementById('fullscreen-img');
                const header = document.getElementById('fullscreen-header');
                const footer = document.getElementById('fullscreen-footer');
                const fileName = document.getElementById('file-name');

                fullscreenImg.src = imageList[currentIndex];
                const world = worldList[currentIndex].name;
                const link = worldList[currentIndex].link;
                header.innerHTML = `<h2>${world}</h2><h3><a href='${link}' style='color: white;'>${link}</a></h3>`;
                footer.innerHTML = `${worldList[currentIndex].index + 1} / ${worldList[currentIndex].total}`;
                fileName.innerText = imageList[currentIndex].split('/').pop();
            }

            document.addEventListener('keydown', function(event) {
                if (document.getElementById('fullscreen').style.display === 'flex') {
                    if (event.key === 'ArrowRight') {
                        showNextImage();
                    } else if (event.key === 'ArrowLeft') {
                        showPrevImage();
                    } else if (event.key === 'Escape') {
                        hideFullscreen();
                    }
                }
            });

            function initImageList() {
                imageList = Array.from(document.querySelectorAll('.image-item img')).map(img => img.src);
                worldList = Array.from(document.querySelectorAll('.image-item img')).map(img => ({
                    name: img.dataset.worldName.replace('\\\\', ''),
                    link: img.dataset.worldLink,
                    index: parseInt(img.dataset.index),
                    total: parseInt(img.dataset.total)
                }));
            }

            window.onload = initImageList;
        </script>
    </head>
    <body>
    <div id="fullscreen" class="fullscreen" onclick="hideFullscreen()">
        <div id="fullscreen-header" class="header"></div>
        <div id="fullscreen-container" class="container">
            <img id="fullscreen-img" src="">
        </div>
        <span id="file-name"></span>
        <div id="fullscreen-footer" class="footer"></div>
    </div>
    """

    index = 0
    for date, worlds in sorted(data_by_date.items()):
        html_content += f"<h1>{date}</h1>"
        for world_id, data_list in worlds.items():
            world_info = data_list[0][1]['world']
            world_name_id = f"{world_info['name']}"
            world_link = f"https://vrchat.com/home/world/{world_info['id']}"
            html_content += f"<h2>{world_name_id}</h2>"
            html_content += f"<h3><a href='{world_link}'>{world_link}</a></h3>"
            html_content += "<div class='image-container'>"
            total_images = len(data_list)
            for idx, (file_path, parsed_data) in enumerate(data_list):
                file_name = os.path.basename(file_path)
                file_path2 = file_path.replace('\\', '/').replace("'", "\\'")
                world_name_id_escaped = world_name_id.replace("'", "\\'").replace('"', '&quot;')
                world_link_escaped = world_link.replace("'", "\\'").replace('"', '&quot;')
                html_content += f"""
                <div class='image-item'>
                    <img src="{file_path2}" data-world-name="{world_name_id_escaped}" data-world-link="{world_link_escaped}" data-index="{idx}" data-total="{total_images}" onclick="showFullscreen('{file_path2}', {index}, '{world_name_id_escaped}', '{world_link_escaped}', '{date}', {total_images})">
                    <span>{file_name}</span>
                </div>
                """
                index += 1
            html_content += "</div>"

    html_content += "</body></html>"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"성공!! -> {output_file}")


def main():
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
        if not os.path.isdir(folder_path):
            print("실패!! 유효한 폴더 경로를 드래그하세요.")
            print()
            print()
            print('종료하려면 아무 키나 누르세요...')
            msvcrt.getch()
    else:
        print("실패!! 폴더를 exe 파일 위로 드래그하세요.")
        print()
        print()
        print('종료하려면 아무 키나 누르세요...')
        msvcrt.getch()
        
    pattern = r'.*\\(.*)'
    output_html_file = f'{re.search(pattern, folder_path).group(1)}.html'

    data_by_date = process_folder(folder_path)
    generate_html(data_by_date, output_html_file)
    
    print()
    print()
    print('종료하려면 아무 키나 누르세요...')
    msvcrt.getch()
    
if __name__ == "__main__":
    main()


