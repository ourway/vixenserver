function FileAPI (t, d, f) {

    var fileList = t,
        fileField = f,
        dropZone = d,
        fileQueue = new Array()
        preview = null;


    this.init = function () {
        fileField.onchange = this.addFiles;
        dropZone.addEventListener("dragenter",  this.stopProp, false);
        dropZone.addEventListener("dragleave",  this.dragExit, false);
        dropZone.addEventListener("dragover",  this.dragOver, false);
        dropZone.addEventListener("drop",  this.showDroppedFiles, false);
    }

    this.addFiles = function () {
        addFileListItems(this.files);
    }

    this.showDroppedFiles = function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var files = ev.dataTransfer.files;
        addFileListItems(files);
    }

    this.clearList = function (ev) {
        ev.preventDefault();
        while (fileList.childNodes.length > 0) {
            fileList.removeChild(
                fileList.childNodes[fileList.childNodes.length - 1]
            );
        }
    }

    this.dragOver = function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.style["backgroundColor"] = "#eee";
        this.style["borderColor"] = "#fff";
        this.style["color"] = "#333";
    }

    this.dragExit = function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        dropZone.style["backgroundColor"] = "#FEFEFE";
        dropZone.style["borderColor"] = "#CCC";
        dropZone.style["color"] = "#333"
    }

    this.stopProp = function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
    }

    this.uploadQueue = function (ev) {
        ev.preventDefault();
        while (fileQueue.length > 0) {
            var item = fileQueue.pop();
            var p = document.createElement("p");
            p.className = "loader";
            var pText = document.createTextNode("Uploading...");
            p.appendChild(pText);
            item.li.appendChild(p);
            if (item.file.size < 4166656) {
                uploadFile(item.file, item.li);
            } else {
                p.textContent = "File too large";
                p.style["color"] = "red";
            }
        }
    }

    var addFileListItems = function (files) {
        for (var i = 0; i < files.length; i++) {
            var fr = new FileReader();
            fr.file = files[i];
            fr.onloadend = showFileInList;
            fr.readAsDataURL(files[i]);
        }
    }

    var showFileInList = function (ev) {
        var file = ev.target.file;
        if (file) {
            var li = document.createElement("li");
            if (file.type.search(/image\/.*/) != -1) {
                var thumb = new Image();
                thumb.src = ev.target.result;
                thumb.addEventListener("mouseover", showImagePreview, false);
                thumb.addEventListener("mouseout", removePreview, false);
                li.appendChild(thumb);
            }
            var h3 = document.createElement("h3");
            var h3Text = document.createTextNode(file.name);
            h3.appendChild(h3Text);
            li.appendChild(h3)
            var p = document.createElement("p");
            var pText = document.createTextNode(
                "File type: ("
                + file.type + ") - " +
                Math.round(file.size / 1024) + "KB"
            );
            p.appendChild(pText);
            li.appendChild(p);
            var divLoader = document.createElement("progress");
            divLoader.className = "loadingIndicator";
            divLoader.value = "0";
            divLoader.max = "100";

            li.appendChild(divLoader);
            fileList.appendChild(li);
            fileQueue.push({
                file : file,
                li : li
            });
        }
    }

    var showImagePreview = function (ev) {
        var div = document.createElement("div");
        div.style["top"] = (ev.pageY + 10) + "px";
        div.style["left"] = (ev.pageX + 10) + "px";
        div.style["opacity"] = 0;
        div.className = "imagePreview";
        var img = new Image();
        img.src = ev.target.src;
        div.appendChild(img);
        document.body.appendChild(div);
        document.body.addEventListener("mousemove", movePreview, false);
        preview = div;
        fadePreviewIn();
    }

    var movePreview = function (ev) {
        if (preview) {
            preview.style["top"] = (ev.pageY + 10) + "px";
            preview.style["left"] = (ev.pageX + 10) + "px";
        }
    }

    var removePreview = function (ev) {
        document.body.removeEventListener("mousemove", movePreview, false);
        document.body.removeChild(preview);
    }

    var fadePreviewIn = function () {
        if (preview) {
            var opacity = preview.style["opacity"];
            for (var i = 10; i < 250; i = i+1) {
                (function () {
                    var level = i;
                    setTimeout(function () {
                        preview.style["opacity"] = opacity + level / 250;
                    }, level);
                })();
            }
        }
    }

    var uploadFile = function (file, li) {
        if (li && file) {
            var xhr = new XMLHttpRequest(),
                upload = xhr.upload;
            upload.addEventListener("progress", function (ev) {
                if (ev.lengthComputable) {
                    var loader = li.getElementsByTagName("progress")[0];
                    var current_val = (ev.loaded/ev.total) * 100
                    loader.setAttribute("value", '"' + current_val + '"' );
                    //document.append('<div>' + current_val + '</div>');
                     //alert(()
                }
            }, false);
            function checkData()
            {
                if (xhr.readyState == 4 ) {
                    //alert('completed!');
                    $('p.loader').text('Completed');
                    $('p.loader').css('color','green');
                    $('.loadingIndicator').css('color','#3b5998');
                    var gid=$('#photo_upload_gid_holder').attr('gid');
                    //alert(gid);
                    //setTimeout('', 1000);
                    //window.location= "show/" + gid;
                }
            }
            upload.addEventListener("error", function (ev) {console.log(ev);}, false);
            xhr.open(
                "post",
                "../utils/upload_to_gallery"+location.search
                );
            xhr.setRequestHeader("Cache-Control", "no-cache");
            xhr.setRequestHeader("Content-type", file.type); 
            xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
            xhr.setRequestHeader("X-File-Name", file.name);
            upload.addEventListener("load", function (ev) {
                var ps = li.getElementsByTagName("p");
                var div = li.getElementsByTagName("progress")[0];
                //div.style["width"] = "100%";
                div.style["backgroundColor"] = "#A4D0FF";
            }, false);
            xhr.send(file);
            xhr.onreadystatechange = checkData;

        }
    }

}

window.onload = function () {
    if (typeof FileReader == "undefined") alert ("Sorry your browser does not support the File API and this demo will not work for you");
    FileAPI = new FileAPI(
        document.getElementById("fileList"),
        document.getElementById("fileDrop"),
        document.getElementById("fileField")
    );
    FileAPI.init();
    var reset = document.getElementById("reset");
    reset.onclick = FileAPI.clearList;
    var upload = document.getElementById("upload");
    upload.onclick = FileAPI.uploadQueue;
}

