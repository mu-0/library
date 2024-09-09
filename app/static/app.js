document.getElementById('myForm').addEventListener('submit', function(event) {
		event.preventDefault(); // Prevents the page from reloading

		// Collect form data
		const formData = new FormData(this);

		// Send form data via fetch to the backend
		fetch('/get_data', {
method: 'POST',
body: formData
})
		.then(response => response.json())
		.then(data => {
			const base64Image = data.image_b64;
			// Update the image source with the new image URL from the server
			document.getElementById('dynamicImage').src = "data:image/jpeg;base64," + base64Image;
			});
		});

const fileInput= document.getElementById('fileInput');
const fileList = document.getElementById('fileList');

// Event listener to handle file selection
fileInput.addEventListener('change', function(event) {
		fileList.innerHTML = ''; // Clear the previous list

		// Get the selected files from the input
		const files = event.target.files;

		// Iterate over the files and filter by extension
		for (let i = 0; i < files.length; i++) {
		const file = files[i];

		// Check file extension (e.g., .png, .jpg, .txt)
		if (file.name.endsWith('.pdf') || file.name.endsWith('.djvu') ) {
		const li = document.createElement('li');
		li.textContent = file.name;
		fileList.appendChild(li);
		}
		}
});
