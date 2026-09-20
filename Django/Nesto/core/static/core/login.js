function handleGoogleLogin(response) {
    console.log("Google login successful!");
        const data = JSON.parse(atob(response.credential.split('.')[1]));
        localStorage.setItem("nestoUserName", data.name);
        localStorage.setItem("nestoUserEmail", data.email);
        window.location.href = "/username/";
    
}