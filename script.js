async function loadPosts() {

    const response =
        await fetch("/api/posts");

    const posts =
        await response.json();


    const container =
        document.getElementById("posts");


    container.innerHTML = "";


    if (posts.length === 0) {

        container.innerHTML = `
            <div class="empty">
                <h3>No posts yet</h3>
                <p>Be the first person to create a post!</p>
            </div>
        `;

        return;

    }


    posts.forEach(post => {

        const div =
            document.createElement(
                "div"
            );


        div.className =
            "post";


        div.innerHTML = `

            <h2>
                ${post.title}
            </h2>

            <p>
                ${post.content}
            </p>

            <div class="post-info">

                By ${post.username}

                <br>

                ${post.created_at}

            </div>

            <br>

            <a
                class="button"
                href="/post.html?id=${post.id}">

                Read & Comment

            </a>

        `;


        container.appendChild(
            div
        );

    });

}


async function logout() {

    const token =
        localStorage.getItem(
            "token"
        );


    if (token) {

        await fetch(
            "/api/logout",
            {
                method: "POST",

                headers: {
                    "Authorization":
                        "Bearer " + token
                }
            }
        );

    }


    localStorage.removeItem(
        "token"
    );

    localStorage.removeItem(
        "username"
    );


    window.location =
        "/";

}


async function checkLogin() {

    const token =
        localStorage.getItem(
            "token"
        );


    const loginLink =
        document.getElementById(
            "loginLink"
        );

    const registerLink =
        document.getElementById(
            "registerLink"
        );

    const logoutButton =
        document.getElementById(
            "logoutButton"
        );


    if (
        token &&
        loginLink &&
        registerLink &&
        logoutButton
    ) {

        loginLink.style.display =
            "none";

        registerLink.style.display =
            "none";

        logoutButton.style.display =
            "inline-block";

    }

}


if (
    document.getElementById(
        "posts"
    )
) {

    loadPosts();

}


checkLogin();