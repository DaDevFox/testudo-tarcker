import "@/styles/globals.css";
import styles from "@/styles/forgot-password.module.css";
import Navbar from "@/components/Navbar";

export default function Forgot(props) {
  return (
    <main className="main">
      <Navbar />
      
      <div className={styles.title_container}>
        <h1>Forgot Password?</h1>
        <h1>Enter username and we'll send you a reset link!</h1>
        <h1>Username: <input></input> </h1> 
      </div>




        <br /> <br /> forgot password? <br /> go to hell!
    </main>
  );
}
