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

	// This is the most important event, the event that gives access to files
	dropZone.addEventListener("drop", function (e) {
		e.preventDefault();
		dropZone.classList.remove(hoverClassName);

		const files = Array.from(e.dataTransfer.files);
		if (files.length > 0) {
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
		}
	});
})();
