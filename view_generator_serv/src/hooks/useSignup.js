import { useState } from "react";
import { useAuthContext } from "./useAuthContext";
import axios from "axios";

export const useSignup = () => {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const { dispatch } = useAuthContext();

  const signup = async (username, password) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        "https://login-service-v2-935294039360.us-central1.run.app/register/",
        {
          username,
          password,
        }
      );

      if (response.status === 201) {
        // Registration was successful
        console.log(response.data.message);

        // Automatically log the user in by storing their info
        const userData = {
          username, // Include the username or any relevant data
        };

        localStorage.setItem("user", JSON.stringify(userData));
        dispatch({ type: "LOGIN", payload: userData });

        setIsLoading(false);
      } else {
        throw new Error("Unexpected response status");
      }
    } catch (error) {
      setIsLoading(false);
      if (error.response && error.response.status === 400) {
        setError("Username already exists or error creating user.");
      } else if (error.response) {
        setError(error.response.data.message || "An error occurred.");
      } else if (error.request) {
        console.error("No response received:", error.request);
        setError("Unable to connect to the server. Please try again later.");
      } else {
        setError(error.message);
      }
    }
  };

  return { signup, isLoading, error };
};
