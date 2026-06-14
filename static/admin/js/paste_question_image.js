document.addEventListener("DOMContentLoaded", function () {

    const fileInput = document.querySelector(
        'input[type="file"][name="question_image"]'
    );

    if (!fileInput) {
        return;
    }

    const helpText = document.createElement("div");

    helpText.style.marginTop = "8px";
    helpText.style.color = "#0b5ed7";
    helpText.style.fontWeight = "600";

    helpText.innerText =
        "Tip: You can upload an image, or copy an image and press Ctrl + V on this page.";

    fileInput.parentNode.appendChild(helpText);

    document.addEventListener("paste", function (event) {

        const clipboardItems = event.clipboardData.items;

        if (!clipboardItems) {
            return;
        }

        for (let i = 0; i < clipboardItems.length; i++) {

            const item = clipboardItems[i];

            if (item.type.indexOf("image") === 0) {

                const blob = item.getAsFile();

                const file = new File(
                    [blob],
                    "question_image_" + Date.now() + ".png",
                    {
                        type: blob.type
                    }
                );

                const dataTransfer = new DataTransfer();

                dataTransfer.items.add(file);

                fileInput.files = dataTransfer.files;

                alert("Image pasted successfully. Now save the question.");

                event.preventDefault();

                break;
            }
        }

    });

});
