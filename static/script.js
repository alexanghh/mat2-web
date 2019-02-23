"use strict";

(function () {
	const dropZone = document.body;
	if (!dropZone) {
		return;
	}

	const hoverClassName = "hover";

	// Handle drag* events to handle style
	// Add the css you want when the class "hover" is present
	dropZone.addEventListener("dragenter", function (e) {
		e.preventDefault();
		dropZone.classList.add(hoverClassName);
	});

	dropZone.addEventListener("dragover", function (e) {
		e.preventDefault();
		dropZone.classList.add(hoverClassName);
	});

	dropZone.addEventListener("dragleave", function (e) {
		e.preventDefault();
		dropZone.classList.remove(hoverClassName);
	});

	// Handle copy/paste
	dropZone.addEventListener("paste", function (e) {
		e.preventDefault();

		if (e.clipboardData.items.length != 1) {
			return
		}

		const item = e.clipboardData.items[0];
		if (item.type.indexOf("image") == -1) {
			return;
		}

		fetch('/', {
			method: 'POST',
			body: item.getAsFile(),
		})
			.then(response => response.text())
			.then(body => {  // Yes, this is ugly
				document.open()
				document.write(body)
				document.close()
			})

	});

	dropZone.addEventListener("drop", function (e) {
		e.preventDefault();
		dropZone.classList.remove(hoverClassName);

		const files = Array.from(e.dataTransfer.files);
		if (files.length != 1 ) {
			return;
		}
		const data = new FormData();
		for (const file of files) {
			data.append('file', file);
		}

		fetch('/', {
			method: 'POST',
			body: data,
		})
			.then(response => response.text())
			.then(body => {  // Yes, this is ugly
				document.open()
				document.write(body)
				document.close()
			})
	});
})();
